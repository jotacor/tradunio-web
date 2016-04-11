#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on April 11, 2016
@author: jotacor
"""

from app import db
from bs4 import BeautifulSoup
from ComunioPy import Comunio
from ConfigParser import ConfigParser
from datetime import date, timedelta, datetime
from ..models import User, Userdata, Transaction, Player, Club
from operator import itemgetter
import re
import requests

FILTRO_STOP = 0.05
BUY_LIMIT = 1.2
MIN_STREAK = 20

config = ConfigParser()
config.read('config.conf')
# c_user = config.get('comunio', 'user')
# c_passwd = config.get('comunio', 'passwd')
# c_user_id = config.getint('comunio', 'user_id')
# community_id = config.getint('comunio', 'community_id')
# fr_email = config.get('comunio', 'fr_email')
# to_email = config.get('comunio', 'to_email')
# admin_email = config.get('comunio', 'admin_email').split(',')
# max_players = config.getint('comunio', 'max_players')
#com = Comunio(c_user, c_passwd, c_user_id, community_id, 'BBVA')
today = date.today()


def update(login, passwd):
    """
    Update the database with new data.
    """
    com = Comunio(login, passwd, 'BBVA')
    users = set_users_data(com)
    set_transactions(com)
    for user in users:
        players = set_user_players(com, user)
        for player in players:
            if player.club_id == 25:
                # Player is not in Primera División
                continue
            set_player_data(player_id=player.id, playername=player.name)




def buy():
    max_gameday = db.simple_query('SELECT MAX(gameday) from points')[0][0]
    players_on_sale = sorted(com.players_onsale(com.community_id, only_computer=False), key=itemgetter(2),
                             reverse=True)
    gamedays = [('%3s' % gameday) for gameday in range(max_gameday - 4, max_gameday + 1)]
    bids = check_bids_offers(kind='bids')
    table = list()
    for player in players_on_sale:
        player_id, playername, team_id, team, min_price, market_price, points, dat, owner, position = player
        to_buy = colorize_boolean(check_buy(player_id, playername, min_price, market_price))
        last_points = db.simple_query(
            'SELECT p.gameday,p.points \
            FROM players pl INNER JOIN points p ON p.idp=pl.idp AND pl.idp = "%s" \
            ORDER BY p.gameday DESC LIMIT 5' % player_id)[::-1]

        if not last_points and not db.rowcount('SELECT idp FROM players WHERE idp = %s' % player_id):
            set_new_player(player_id, playername, position, team_id)
            _, last_points = set_player_data(player_id=player_id, playername=playername)
            last_points = last_points[-5:]
        elif not last_points:
            _, last_points = set_player_data(player_id=player_id, playername=playername)
            last_points = last_points[-5:]
        elif team_id == 25:
            continue

        streak = sum([int(x[1]) for x in last_points])
        last_points = {gameday: points for (gameday, points) in last_points}
        last_points_array = list()
        for gameday in range(max_gameday - 4, max_gameday + 1):
            points = last_points.get(gameday, 0)
            points = colorize_points(points)
            last_points_array.append(points)

        prices = db.simple_query(
            'SELECT p.date,p.price \
            FROM players pl INNER JOIN prices p ON p.idp=pl.idp AND pl.idp = "%s" \
            ORDER BY p.date ASC' % player_id)
        day, week, month = 0, 0, 0

        try:
            day = colorize_profit(calculate_profit(prices[-2][1], market_price))
            week = colorize_profit(calculate_profit(prices[-8][1], market_price))
            month = colorize_profit(calculate_profit(prices[-30][1], market_price))
        except IndexError:
            pass

        bid, extra_price = 0.0, colorize_profit(0.0)
        if player_id in bids:
            bid = bids[player_id][2]
            extra_price = colorize_profit(bids[player_id][3])

        table.append([playername, position, to_buy, owner, month, week, day,
                      market_price, min_price, bid, extra_price, ' '.join(last_points_array), streak])


def sell():
    max_gameday = db.simple_query('SELECT MAX(gameday) from points')[0][0]
    gamedays = [('%3s' % gameday) for gameday in range(max_gameday - 4, max_gameday + 1)]
    console, table = list(), list()
    players = get_user_players(user_id=com.myid)
    offers = check_bids_offers(kind='offers')
    for player in players:
        player_id, playername, club_id, club_name, position = player
        bought_date, bought_price, market_price, to_sell, profit = check_sell(player_id)

        last_points = db.simple_query(
            'SELECT p.gameday,p.points \
            FROM players pl INNER JOIN points p ON p.idp=pl.idp AND pl.idp = "%s" \
            ORDER BY p.gameday DESC LIMIT 5' % player_id)[::-1]

        if not last_points and not db.rowcount('SELECT idp FROM players WHERE idp = %s' % player_id):
            set_new_player(player_id, playername, position, club_id)
            _, last_points = set_player_data(player_id=player_id, playername=playername)
            last_points = last_points[-5:]
        elif not last_points:
            _, last_points = set_player_data(player_id=player_id, playername=playername)
            last_points = last_points[-5:]

        streak = sum([int(x[1]) for x in last_points])
        last_points = {gameday: points for (gameday, points) in last_points}
        last_points_array = list()
        for gameday in range(max_gameday - 4, max_gameday + 1):
            points = last_points.get(gameday, 0)
            points = colorize_points(points)
            last_points_array.append(points)

        prices = db.simple_query(
            'SELECT p.date,p.price \
            FROM players pl INNER JOIN prices p ON p.idp=pl.idp AND pl.idp = "%s" \
            ORDER BY p.date ASC' % player_id)
        day, week, month = 0, 0, 0

        try:
            day = colorize_profit(calculate_profit(prices[-2][1], market_price))
            week = colorize_profit(calculate_profit(prices[-8][1], market_price))
            month = colorize_profit(calculate_profit(prices[-30][1], market_price))
        except IndexError:
            pass

        to_sell = colorize_boolean(to_sell)
        profit_color = colorize_profit(profit)

        offer, extra_price, who = 0.0, colorize_profit(0.0), '-'
        if player_id in offers:
            who = offers[player_id][1]
            offer = offers[player_id][2]
            extra_price = colorize_profit(offers[player_id][3])

        table.append(
            [playername, position, to_sell, bought_date, month, week, day, ' '.join(last_points_array),
             streak, bought_price, market_price, profit_color, offer, who, extra_price])


def get_users_data():
    """
    Gets data of the users.
    :return: {{user_id: username, user_points, teamvalue, money, maxbid}}
    """
    last_date = db.simple_query('SELECT MAX(date) FROM user_data LIMIT 1')[0][0]
    if last_date == today:
        users_data = dict()
        users = db.simple_query('SELECT u.idu,u.name,d.points,d.money,d.teamvalue,d.maxbid \
                        FROM users u, user_data d WHERE u.idu=d.idu AND date = "%s"' % last_date)
        for user in users:
            user_id, username, user_points, money, teamvalue, maxbid = user
            users_data[user_id] = [username, user_points, teamvalue, money, maxbid]
    else:
        users_data = set_users_data()

    return users_data


def set_users_data(com):
    """
    Gets the last data of the users from Comunio and saves it to database.
    :return: {{user_id: username, user_points, teamvalue, money, maxbid}}
    """
    users_data = list()
    users_info = com.get_users_info()
    for user in users_info:
        [username, user_id, user_points, teamvalue, money, maxbid] = user
        u = User.query.filter_by(id=user_id).first()
        if not u:
            u = User(id=user_id, name=username)

        ud = Userdata.query.filter_by(id=user_id).filter_by(date=date.today()).first()
        if not ud:
            ud = Userdata(id=u, date=date.today(), points=user_points, money=money, teamvalue=teamvalue, maxbid=maxbid)

        u.userdata.append(ud)
        db.session.add(u)
        db.session.commit()

        users_data.append(u)
    return users_data


def get_user_players(user_id=None):
    """
    Get the players of the users checking first if it is updated in database.
    :param user_id: Id of the user.
    :return: ((player_id, playername, club_id, clubname, position))
    """
    players = db.simple_query('SELECT pl.idp,pl.name,cl.idcl,cl.name,pl.position \
                              FROM players pl, clubs cl, owners o \
                              WHERE o.idp=pl.idp AND pl.idcl=cl.idcl AND o.idu=%s' % user_id)
    return players


def set_user_players(com, user=None):
    """
    Set the players of the user.
    :param user_id: Id of the user.
    :param username: Name of the user.
    :return: [[player_id, playername, club_id, club_name, value, player_points, position]]
    """
    user_players = com.get_user_players(user.id)
    players = list()
    for player in user_players:
        player_id, playername, club_id, club_name, value, player_points, position = player

        c = Club.query.filter_by(id=club_id).first()
        if not c:
            c = Club(id=club_id, name=club_name)

        p = Player.query.filter_by(id=player_id).first()
        if not p:
            p = Player(id=player_id, name=playername, position=position, club=c)

        user.players.append(p)
        db.session.add(user)
        db.session.commit()
        players.append(p)

    return players


def get_player_data(playername=None):
    """
    Get prices from a player
    :param playername: Name of the player.
    :return: [dates], [prices], [points]
    """

    session = requests.session()
    url_comuniazo = 'http://www.comuniazo.com'
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:35.0) Gecko/20100101 Firefox/35.0'
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", 'Referer': url_comuniazo,
               "User-Agent": user_agent}
    url_jugadores = url_comuniazo + '/comunio/jugadores/'
    suffix, lastname = '', ''
    count = 0
    dates, points, prices = list(), list(), list()
    while True and len(dates) < 2:
        playername = check_exceptions(playername)
        req = session.get(url_jugadores + playername.replace(" ", "-").replace(".", "").replace("'", "") + suffix,
                          headers=headers).content
        dates_re = re.search("(\"[0-9 ][0-9] de \w+\",?,?)+", req)
        try:
            dates = dates_re.group(0).replace('"', '').split(",")
            dates = translate_dates(dates)
        except AttributeError:
            if count == 0:
                suffix = '-2'
                count += 1
                continue
            elif count == 1:
                lastname = playername.split(" ")[1]
                playername = playername.split(" ")[0]
                suffix = ''
                count += 1
                continue
            elif count == 2:
                playername = lastname
                count += 1
                continue

        data_re = re.search("data: \[(([0-9nul]+,?)+)\]", req)
        if data_re is None:
            pass
        for price in data_re.group(1).split(','):
            try:
                prices.append(int(price))
            except ValueError:
                # No price
                pass

        try:
            html = BeautifulSoup(req, "html.parser")
            points_rows = html.find('table', {'class': 'points-list'}).find_all('tr')
            for row in points_rows:
                gameday = int(row.td.text)
                if row.div:
                    points.append([gameday, int(row.div.text)])
                else:
                    points.append([gameday, 0])
        except AttributeError:
            # Player without points
            pass

        if suffix == '-2' or len(dates) > 2:
            break
        else:
            suffix = '-2'

    return dates, prices, points


def set_player_data(player_id=None, playername=None):
    """
    Sets prices and points for all the players of the user
    :param player_id: Id of the football player
    :param playername: Football player name
    :return: Players of the user id
    """
    days_left = days_wo_price(player_id)
    prices, points = list(), list()
    if days_left:
        dates, prices, points = get_player_data(playername=playername)
        if days_left >= 365:
            days_left = len(dates)

        if not db.rowcount('SELECT idp FROM players WHERE idp=%s' % player_id):
            playername, position, club_id, price = com.get_player_info(player_id)
            set_new_player(player_id, playername, position, club_id)

        db.many_commit_query('INSERT IGNORE INTO prices (idp,date,price) VALUES (%s' % player_id + ',%s,%s)',
                             zip(dates[:days_left], prices[:days_left]))
        for point in points:
            db.nocommit_query('INSERT INTO points (idp,gameday,points) VALUES (%s,%s,%s) \
                              ON DUPLICATE KEY UPDATE points=%s' % (player_id, point[0], point[1], point[1]))
        db.commit()

    return prices, points


def set_new_player(player_id, playername, position, team_id):
    """
    Set new player in the database.
    :param player_id:
    :param playername:
    :param position:
    :param team_id:
    """
    db.commit_query('INSERT IGNORE INTO players (idp,name,position,idcl) VALUES (%s,"%s","%s",%s)'
                    % (player_id, playername, position, team_id))


def set_transactions(com):
    """
    Save to database all the transactions.
    """
    until_date = db.session.query(db.func.max(Transaction.date).label('date')).first().date
    if not until_date:
        until_date = date.today() - timedelta(days=120)
    until_date = until_date - timedelta(days=10)
    news = com.get_news(until_date)
    for new in news:
        ndate, title, text = new
        if 'Fichajes' not in title:
            continue
        pattern = re.compile(
            ur'(?:(?:\\n)?([(\S+ )]+?)(?: cambia por )([0-9\.,]*?)(?: .*? de )(.+?) a (.+?)\.)',
            re.UNICODE)
        transactions = re.findall(pattern, text)
        for trans in transactions:
            playername, value, fr, to = trans
            value = int(value.replace('.', ''))
            playername = playername.strip()
            try:
                player = db.session.query(Player).filter(Player.name.like('%'+playername+'%')).first()
                if 'Computer' in fr:
                    kind = 'Buy'
                    user = db.session.query(User).filter(User.name.like('%'+to+'%')).first()
                    t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                    db.session.add(t)
                    db.session.commit()
                elif 'Computer' in to:
                    kind = 'Sell'
                    user_id = db.simple_query('SELECT idu FROM users WHERE name LIKE "%%%s%%"' % fr)[0][0]
                    db.commit_query(
                        'INSERT IGNORE INTO transactions (idp, idu, type, price, date) VALUES (%s,%s,"%s",%s,"%s")'
                        % (player_id, user_id, kind, value, ndate))
                else:
                    kind = 'Buy'
                    user_id = db.simple_query('SELECT idu FROM users WHERE name LIKE "%%%s%%"' % to)[0][0]
                    db.commit_query(
                        'INSERT IGNORE INTO transactions (idp, idu, type, price, date) VALUES (%s,%s,"%s",%s,"%s")'
                        % (player_id, user_id, kind, value, ndate))
                    user_id = db.simple_query('SELECT idu FROM users WHERE name LIKE "%%%s%%"' % fr)[0][0]
                    kind = 'Sell'
                    db.commit_query(
                        'INSERT IGNORE INTO transactions (idp, idu, type, price, date) VALUES (%s,%s,"%s",%s,"%s")'
                        % (player_id, user_id, kind, value, ndate))
            except IndexError:
                # Player selled before having in database
                pass


def check_bids_offers(kind=None):
    """
    Check if you have offers for your players or show you the bids made for other players.
    :param kind:
    :return:
    """
    bids_offers = dict()
    if kind == 'bids':
        from_you = com.bids_from_you()
        for bid in from_you:
            player_id, playername, owner, team_id, team, price, bid_date, trans_date, status = bid
            if status == 'Pendiente' or status == 'Pending':
                _, prices, _ = get_player_data(playername=playername)
                extra_price = calculate_profit(prices[0], price)
                bids_offers[player_id] = [playername, owner, price, extra_price]
    elif kind == 'offers':
        to_you = sorted(com.bids_to_you())
        player_ant, price_ant = 0, 0
        for offer in to_you:
            player_id, playername, who, team_id, team, price, bid_date, trans_date, status = offer
            if status == 'Pendiente' or status == 'Pending':
                if player_ant == player_id and price < price_ant:
                    # Only saves the max offer for every player
                    continue
                precio_compra = db.simple_query(
                    'SELECT price FROM transactions WHERE idp=%s AND type="Buy" ORDER BY date DESC LIMIT 1'
                    % player_id)

                if not precio_compra:
                    first_date = db.simple_query('SELECT MIN(date) FROM transactions')[0][0]
                    precio_compra = db.simple_query(
                        'SELECT price FROM prices WHERE idp=%s AND date>"%s" ORDER BY date ASC LIMIT 1'
                        % (player_id, first_date))

                profit = calculate_profit(precio_compra[0][0], price)
                bids_offers[player_id] = [playername, who, price, profit]
                player_ant, price_ant = player_id, price

    return bids_offers


def check_buy(player_id, playername, min_price, mkt_price):
    """
    Check if it's a good deal buy a player
    :param player_id: Id of the football player.
    :param playername: Name of the football player.
    :param min_price: Minimum price requested.
    :param mkt_price: Market price.
    :return: True/False if it is a good deal to buy it.
    """
    _, points = set_player_data(player_id=player_id, playername=playername)
    first_date = db.simple_query('SELECT MIN(date) FROM transactions')[0][0]
    last_days = (today - timedelta(days=3))
    prices = db.simple_query(
        'SELECT pr.price,pr.date FROM prices pr,players pl \
         WHERE pl.idp=pr.idp AND pl.idp=%s AND pr.date>"%s" ORDER BY pr.date ASC' % (player_id, first_date))
    max_h = 0
    fecha = date(1970, 01, 01)
    for row in prices:
        price, dat = row
        if price > max_h:
            max_h = price
            fecha = dat

    streak = sum([int(point) for gameday, point in points[-5:]])
    # Si la fecha a la que ha llegado es la de hoy (max_h) y
    #   el precio que solicitan no es superior al de mercado+BUY_LIMIT, se compra
    if fecha > last_days and min_price < (mkt_price * BUY_LIMIT) and streak > MIN_STREAK:
        return True
    else:
        return False


def check_sell(player_id):
    """
    Check the rentability of our players.
    :param player_id: Football player id.
    :return: bought_date, bought_price, current_price, sell, profit
    """
    sell = False
    try:
        bought = db.simple_query(
            'SELECT date,price FROM transactions \
            WHERE idp=%s AND type="Buy" \
            ORDER BY date DESC LIMIT 1' % player_id)[0]
    except IndexError:
        first_date = db.simple_query('SELECT MIN(date) FROM transactions')[0][0]
        current_price = float(db.simple_query(
            'SELECT price FROM prices \
            WHERE idp=%s \
            ORDER BY date DESC LIMIT 1' % player_id)[0][0])
        init_price = float(db.simple_query(
            'SELECT price FROM prices \
            WHERE idp=%s AND date>"%s" \
            ORDER BY date ASC LIMIT 1' % (player_id, first_date))[0][0])
        profit = calculate_profit(init_price, current_price)

        return '-', init_price, current_price, sell, profit

    prev_price, stop, price = 0, 0, 0
    bought_date, bought_price = bought[0], float(bought[1])

    prices = db.simple_query(
        'SELECT idp,date,price \
        FROM prices \
        WHERE idp=%s AND date>="%s" \
        ORDER BY date ASC' % (player_id, bought_date))

    for price_data in prices:
        price = float(price_data[2])
        if price > prev_price:
            prev_price = price
            stop = int(prev_price - (prev_price * FILTRO_STOP))

        # Comprobamos si el precio ha roto el stop
        if price < stop:
            sell = True

        # Si el precio del jugador se ha recuperado y ya había entrado en venta, se demarca la venta
        if price > stop and sell:
            sell = False

    # Calculate profit
    profit = calculate_profit(bought_price, price)

    return bought_date, bought_price, price, sell, profit


def translate_dates(dates):
    """
    Translates dates format from 'xx de Month' or 'dd.mm' to date('yyyy-mm-dd')
    :param dates: Array dates from Comuniazo or Comunio.
    :return: [[date,]]
    """
    formatted_dates = list()
    year = str(today.year)
    for dat in dates:
        if dat == '':
            continue
        day = dat[:2]
        mont = dat[6:]
        if int(day) < 10:
            day = '0' + day[1]
        if mont != '':
            # Month from Comuniazo
            month = \
                {'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                 'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                 'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'}[mont]
        else:
            # Month from Comunio
            month = dat[3:5]

        if month + day == '0101' or (formatted_dates and int(month) > formatted_dates[-1].month):
            # One year less
            year = str(today.year - 1)

        p_date = datetime.strptime('%s-%s-%s' % (year, month, day), "%Y-%m-%d").date()
        formatted_dates.append(p_date)
    return formatted_dates


def calculate_profit(price_ago, current_price):
    """
    Calculates the profit of a price regarding a previous one.
    :param price_ago: First price.
    :param current_price: Last price.
    :return: Profit in percentage.
    """
    profit = (current_price - price_ago) / float(price_ago) * 100
    return profit


def days_wo_price(player_id):
    """
    Returns the days that the player has not a price in the database.
    :param player_id: Player ID
    :return: Days without price (max 365 days)
    """
    max_date = db.session.query(db.func.max(Price.date).label('max_date')).first().max_date

    try:
        res = (date.today() - max_date).days
    except TypeError:
        res = 365

    if not (0 < res < 365):
        res = 365

    return res


def check_exceptions(playername):
    """
    Fix exceptions for a player name between Comunio and Comuniazo.
    :param playername: Name of the football player.
    :return: Corrected name.
    """
    exceptions = {'Banega': 'Ever Banega', 'Mikel': u'Mikel González', u'Isma López': u'Ismael López'}
    return exceptions.get(playername, playername)
