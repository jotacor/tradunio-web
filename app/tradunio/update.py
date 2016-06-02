#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on April 11, 2016
@author: jotacor
"""

from app import db
from comunio import Comunio
from comuniazo import Comuniazo
from comunio_service import Comunio as ComService
from datetime import date, timedelta
from ..models import User, Userdata, Transaction, Player, Club, Price, Points, Market, Owner, Community, Gameday
import re


def update_all(login, passwd):
    """
    Update the database with new data.
    """
    db.create_all()
    # New players, previous players


    # New prices and points

    # prices = com.get_player_price(playerid=player_id, from_date=year_ago.strftime('%Y-%m-%d'))
    # for price_date, price in prices:
    #     if not Price.query.filter_by(id=player_id).filter_by(date=price_date).count():
    #         pr = Price(id=player_id, date=price_date, price=price)

    # com = Comunio(login, passwd, 'BBVA')

    # if not com.logged:
    #     print "We can't log in, please try again later."
    #     exit(1)

    # users = set_users_data(com)

    # for user in users:
    #     players = set_user_players(com, user)
    #     for player in players:
    #         if player.club_id == 25:
    #             # Player is not in Primera División
    #             continue
    #         set_player_data(com, player_id=player.id, playername=player.name)
    #
    # set_transactions(com)
    # update_market(com=com, user_id=user.id)


def init_database():
    db.create_all()

    year_ago = date.today() - timedelta(days=365)
    comunio = ComService()
    comuniazo = Comuniazo()

    # Basic data info
    u = User(id=1, name='Computer', username='Computer')
    c = Club(id=1, name='Computer')
    db.session.add_all([u, c])
    db.session.commit()

    # Fill in all gamedays
    gamedays = comunio.get_gamedays()
    for gameday in gamedays:
        number, comunio_gameday_id, gamedate, shifted = gameday
        if gamedate.month >= 8 and gamedate.month <=12:
            season = str(gamedate.year)[2:4] + str(gamedate.year + 1)[2:4]
        else:
            season = str(gamedate.year - 1)[2:4] + str(gamedate.year)[2:4]

        if number <= 9:
            number = '0%s' % number

        gameday_id = season + str(number)
        g = Gameday(id=gameday_id, season=season, gameday=number, gamedate=gamedate, shifted=shifted)
        db.session.add(g)

    db.session.commit()

    # Fill in every player of every club
    clubs = comunio.get_clubs()
    for club_id, clubname in clubs:

        if not Club.query.filter_by(id=club_id).count():
            c = Club(id=club_id, name=clubname)
            db.session.add(c)

        players = comunio.get_playersbyclubid(club_id)
        for player in players:
            player_id, playername, points, club_id, price, status, status_info, position, games_played = player
            if not Player.query.filter_by(id=player_id).count():
                p = Player(id=player_id, name=playername, position=position, club=c, status=status,
                           status_info=status_info)
                db.session.add(p)

            dates, prices, points_all = comuniazo.get_player_data(player_id=player_id)

            for date_price, price in zip(dates, prices):
                if not Price.query.filter_by(id=player_id).filter_by(date=date_price).first():
                    pr = Price(id=player_id, date=date_price, price=price)
                    db.session.add(pr)

            for season, gameday, points in points_all:
                if gameday <= 9:
                    gameday = '0%s' % gameday

                gameday_id = season + str(gameday)
                if not Points.query.filter_by(id=player_id).filter_by(gameday_id=gameday_id).count():
                    pt = Points(id=player_id, gameday_id=gameday_id, points=points)
                    db.session.add(pt)
                elif pt.points == 0:
                    pt.points = points
                    db.session.add(pt)

        db.session.commit()


def update_market(com=None, community_id=None, user_id=None):
    """
    Update the database with new data in market.
    """
    db.create_all()
    com_service = ComService()
    market = com_service.get_market(community_id, user_id)

    for player in market:
        player_id, playername, points, club_id, market_price, min_price, status, injured, position, placed_date, owner_id = player

        c = Club.query.filter_by(id=club_id).first()
        p = Player.query.filter_by(id=player_id).first()
        if not p:
            set_player_data(com, player_id=player_id, playername=playername)

        u = User.query.filter_by(id=owner_id).first()
        m = Market.query.filter_by(owner_id=u.id).filter_by(player_id=player_id).filter_by(date=date.today()).first()
        if not m:
            m = Market(owner_id=u.id, player_id=player_id, date=date.today(), mkt_price=market_price, min_price=min_price)
            db.session.add(m)

        db.session.commit()



def set_users_data(com):
    """
    Gets the last data of the users from Comunio and saves it to database.
    :type com: User
    :return: {{user_id: username, user_points, teamvalue, money, maxbid}}
    """
    users_data = list()
    users_info = com.get_users_info()

    u = User.query.filter_by(id=1).first()
    if not u:
        u = User(id=1, name='Computer', username='Computer')
        db.session.add(u)
        db.session.commit()

    for user in users_info:
        [name, username, user_id, user_points, teamvalue, money, maxbid] = user
        u = User.query.filter_by(id=user_id).first()
        if not u:
            u = User(id=user_id, name=name, username=username)

        ud = Userdata.query.filter_by(id=user_id).filter_by(date=date.today()).first()
        if not ud:
            ud = Userdata(id=u, date=date.today(), points=user_points, money=money, teamvalue=teamvalue, maxbid=maxbid)

        u.userdata.append(ud)
        db.session.add(u)
        db.session.commit()

        users_data.append(u)
    return users_data


def set_user_players(com, user=None):
    """
    Set the players of the user.
    :param com: Object to ask Comunio
    :param user: Object User
    :return: [[player_id, playername, club_id, club_name, value, player_points, position]]
    """
    user_players = com.get_user_players(user.id)
    players = list()

    # for owner in user.owns:
    #     owner.player.owner = 0
    #     db.session.commit()

    for player in user_players:
        player_id, playername, club_id, club_name, value, player_points, position = player

        c = Club.query.filter_by(id=club_id).first()
        if not c:
            c = Club(id=club_id, name=club_name)

        p = Player.query.filter_by(id=player_id).first()
        if not p:
            p = Player(id=player_id, name=playername, position=position, club=c)

        o = Owner.query.filter_by(player_id=p.id, owner_id=user.id).first()
        if not o:
            o = Owner(player_id=p.id, owner_id=user.id)
            user.owns.append(o)
            db.session.add(user)
            db.session.commit()

        players.append(p)

    return players


def set_player_data(com, player_id=None, playername=None):
    """
    Sets prices and points for all the players of the user
    :param com: Object to ask Comunio
    :param player_id: Id of the football player
    :param playername: Football player name
    :return: Players of the user id
    """
    days_left = days_wo_price(player_id)
    prices, points_all = list(), list()
    if days_left:
        dates, prices, points_all = Comunio.get_player_data(playername)
        if days_left >= 365:
            days_left = len(dates)

        player = Player.query.filter_by(id=player_id).first()
        if not player:
            playername, position, club_id, price = com.get_player_info(player_id)
            player = set_new_player(player_id, playername, position, club_id)

        for dat, price in zip(dates[:days_left], prices[:days_left]):
            if not Price.query.filter_by(id=player.id).filter_by(date=dat).first():
                pr = Price(id=player.id, date=dat, price=price)
                db.session.add(pr)

        for gameday, points in points_all:
            p = Points.query.filter_by(id=player.id).filter_by(gameday=gameday).first()
            if not p:
                pt = Points(id=player.id, gameday=gameday, points=points)
                db.session.add(pt)
            elif p.points == 0:
                p.points = points
                db.session.add(p)

        db.session.commit()

    return prices, points_all


def set_transactions(com):
    """
    Save to database all the transactions.
    """
    until_date = db.session.query(db.func.max(Transaction.date).label('date')).first().date
    if not until_date:
        until_date = date.today() - timedelta(days=120)
    else:
        until_date = until_date - timedelta(days=10)
    news = com.get_news(until_date)
    for new in news:
        ndate, title, text = new
        if 'Fichajes' not in title:
            continue
        pattern = re.compile(
            ur'(?:(?:\\n)?([(\S+ )]+?)(?: cambia por )([0-9\.,]*?)(?: .*? de )(.+?) a (.+?)\.)', re.UNICODE)
        transactions = re.findall(pattern, text)
        for trans in transactions:
            playername, value, fr, to = trans
            value = int(value.replace('.', ''))
            playername = playername.strip()
            try:
                if db.session.query(Player).filter(Player.name.like(playername)).count():
                    player = db.session.query(Player).filter(Player.name.like(playername)).first()
                else:
                    player = db.session.query(Player).filter(Player.name.like('%' + playername + '%')).first()

                if 'Computer' in fr:
                    kind = 'Buy'
                    user = db.session.query(User).filter(User.name.like('%' + to + '%')).first()
                    if not exist_transaction(player, user, kind, value, ndate):
                        t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                        db.session.add(t)
                elif 'Computer' in to:
                    kind = 'Sell'
                    user = db.session.query(User).filter(User.name.like('%' + fr + '%')).first()
                    if not exist_transaction(player, user, kind, value, ndate):
                        t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                        db.session.add(t)
                else:
                    kind = 'Buy'
                    user = db.session.query(User).filter(User.name.like('%' + to + '%')).first()
                    if not exist_transaction(player, user, kind, value, ndate):
                        t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                        db.session.add(t)

                    user = db.session.query(User).filter(User.name.like('%' + fr + '%')).first()
                    kind = 'Sell'
                    if not exist_transaction(player, user, kind, value, ndate):
                        t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                        db.session.add(t)

                db.session.commit()

            except AttributeError:
                # Player selled before having in database
                pass


def exist_transaction(player, user, kind, value, ndate):
    return db.session.query(Transaction).filter(Transaction.player_id == player.id).filter(
        Transaction.user_id == user.id).filter(Transaction.sort == kind).filter(Transaction.price == value).filter(
        Transaction.date == ndate).first()


def days_wo_price(player_id):
    """
    Returns the days that the player has not a price in the database.
    :param player_id: Player ID
    :return: Days without price (max 365 days)
    """
    max_date = db.session.query(db.func.max(Price.date).label('max_date')).first().max_date

    if not max_date:
        res = 365
    else:
        res = (date.today() - max_date).days
        if not (0 < res <= 365):
            res = 365

    return res


def set_new_player(player_id, playername, position, club_id):
    """
    Set new player in the database.
    :param player_id:
    :param playername:
    :param position:
    :param club_id:
    """
    c = Club.query.filter_by(id=club_id).first()
    p = Player(id=player_id, name=playername, position=position, club=c)
    db.session.add(p)
    db.session.commit()
    return p
