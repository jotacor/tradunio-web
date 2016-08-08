#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import date as dt
from datetime import datetime
import json
import re
import requests
import time

Leagues = {'BBVA': 'http://www.comunio.es',
           'Adelante': 'http://www.comuniodesegunda.es',
           'Bundesliga': 'http://www.comunio.de',
           'Bundesliga2': 'http://www.comdue.de',
           'Serie A': 'http://www.comunio.it',
           'Premier League': 'http://www.comunio.co.uk',
           'Liga Sagres': 'http://www.comunio.pt'}

user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102'
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}


class Comunio:
    def __init__(self, username, password, league):
        self.username = username
        self.password = password
        self.domain = Leagues[league]
        self.session = requests.session()
        self.user_id = None
        self.money = None
        self.teamvalue = None
        self.community_id = None
        self.news = list()
        self.urls = {'news': self.domain + '/team_news.phtml',
                     'login': self.domain + '/login.phtml'}
        self.logged = self.login()
        self.urls.update({'team': '%s/teamInfo.phtml?tid=%s' % (self.domain, self.community_id),
                          'player': '%s/playerInfo.phtml?pid=%%s' % self.domain,
                          'trade': '%s/tradableInfo.phtml?tid=%%s' % self.domain,
                          })

    def login(self):
        payload = {'login': self.username, 'pass': self.password, 'action': 'login'}
        req = self.session.post(self.urls['login'], headers=headers, data=payload).content
        if 'puntos en proceso' in req or 'points in process' in req:
            return False

        return self.load_info()

    def load_info(self):
        """ Get info from logged account """
        headers.update({'Referer': self.urls['login']})
        req = self.session.get(self.urls['news'], headers=headers).content
        soup = BeautifulSoup(req, "html.parser")

        estado = soup.find('div', {'id': 'content'}).find('div', {'id': 'manager'}).string
        if estado:
            return False

        [s.extract() for s in soup('strong')]
        if soup.find('div', {'id': 'userid'}) is not None:
            self.user_id = int(soup.find('div', {'id': 'userid'}).p.text.strip()[2:])
            self.money = int(soup.find('div', {'id': 'manager_money'}).p.text.strip().replace(".", "")[:-2])
            self.teamvalue = int(soup.find('div', {'id': 'teamvalue'}).p.text.strip().replace(".", "")[:-2])
            self.community_id = int(soup.find('link')['href'][24:])
            # self.username = soup.find('div', {'id': 'username'}).p.a.text

        return True

    def get_users_info(self):
        """
        Get users info from my community
        @return: [[name, username, user_id, user_points, team_value, money, max_bid],]
        """
        headers.update({'Referer': self.domain + '/standings.phtml'})
        req = self.session.get(self.urls['team'], headers=headers).content
        soup = BeautifulSoup(req, "html.parser")

        money_bids = self.get_money_bids(self.username)

        info = list()
        for row in soup.find('table', cellpadding=2).find_all('tr')[1:]:
            money, max_bid = [0, 0]
            name = row.a.text
            user_id = row.find('a')['href'].split('pid=')[1]
            req = self.session.get(self.urls['player'] % user_id, headers=headers).content
            html_h1 = BeautifulSoup(req, "html.parser").h1.text
            username = re.findall('\((.+)\)', html_h1)[0]
            user_points = int(row.find_all('td')[2].text.replace('.', ''))
            team_value = int(row.find_all('td')[3].text.replace('.', ''))
            for user in money_bids['data']['users']:
                if user['id'] == user_id:
                    money = int(user['dinero'].replace('.', ''))
                    max_bid = int(user['puja'].replace('.', ''))
                    break

            info.append([name, username, int(user_id), user_points, team_value, money, max_bid])

        return info

    def get_user_players(self, user_id):
        """Get user players using his user_id
        @param user_id: Id of the user
        @return: [username, points,[[player_id, name, club, value, points, position],]]
        """
        headers.update({'Referer': self.domain + '/standings.phtml'})
        req = self.session.get(self.urls['player'] % user_id, headers=headers).content
        soup = BeautifulSoup(req, "html.parser")

        players_info = list()
        for i in soup.find('table', cellpadding=2).find_all('tr')[1:]:
            cad = i.find_all('td')
            player_id = int(re.findall('\d+', i.find_all('img')[0]['src'])[0])
            name = cad[2].text.strip()
            club = cad[3].find('img')['alt']
            club_id = int(re.findall('\d+', i.find_all('img')[1]['src'])[0])
            value = float(cad[4].text.replace(".", ""))
            totalpoints = float(cad[5].text)
            position = self.translate_position(cad[6].text)
            players_info.append([player_id, name, club_id, club, value, totalpoints, position])

        return players_info

    @staticmethod
    def get_player_data(playername=None):
        """
        Get historical prices from a player from Comuniazo
        :param playername: Name of the player.
        :return: [dates], [prices], [points]
        """
        session = requests.session()
        url_comuniazo = 'http://www.comuniazo.com'
        headers.update({'Referer': url_comuniazo})
        url_jugadores = url_comuniazo + '/comunio/jugadores/'
        suffix, lastname = '', ''
        count = 0
        dates, points, prices = list(), list(), list()
        while True and len(dates) < 2:
            playername = Comunio.check_exceptions(playername)
            req = session.get(url_jugadores + playername.replace(" ", "-").replace(".", "").replace("'", "") + suffix,
                              headers=headers).content
            dates_re = re.search("(\"[0-9 ][0-9] de \w+\",?,?)+", req)
            try:
                dates = dates_re.group(0).replace('"', '').split(",")
                dates = Comunio.translate_dates(dates)
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

    def get_player_info(self, player_id):
        """'
        Get info football player using a ID
        @return: [playername,position,team_id,price]
        :param player_id: Id of the football player.
        """
        headers.update({'Referer': self.urls['news']})
        req = self.session.get(self.urls['trade'] % player_id, headers=headers).content
        soup = BeautifulSoup(req, "html.parser")
        playername = soup.title.text.strip()
        rows = soup.find('table', cellspacing=1).find_all('tr')
        position = self.translate_position(rows[0].find_all('td')[1].text)
        club_id = int(re.findall('\d+', rows[1].find_all('td')[1].img['src'])[0])
        price = 0

        for row in rows:
            try:
                price = int(row.find_all('td')[1].text.replace(".", ""))
                if price > 150000:
                    break
            except ValueError:
                continue

        return [playername, position, club_id, price]

    def get_news(self, until_date=None):
        """ Get all the news until the date until_date included.
        :param until_date: Last date, included, we want the news.
        """
        if not self.news:
            more_news = True
            headers.update({'Referer': self.urls['login']})
            req = self.session.get(self.urls['news'], headers=headers).content
            soup = BeautifulSoup(req, "html.parser")
            newsheader = soup.find_all('div', {'class', 'newsheader'})[1:]
            for index, i in enumerate(soup.find_all('div', {'class', 'article_content_text'})[1:]):
                news_date = datetime.strptime(newsheader[index].span['title'][0:8], "%d.%m.%y").date()
                news_title = newsheader[index].text.split(">")[1].strip()
                if news_date < until_date:
                    more_news = None
                    break
                self.news.append([news_date, news_title, i.text])
            first_news = 10
            while more_news and first_news < 200:
                req = self.session.post(self.urls['news'], headers=headers,
                                        data={'newsAction': 'reload', 'first_news': first_news}).content
                other_news = BeautifulSoup(req, "html.parser")
                newsheader = other_news.find_all('div', {'class', 'newsheader'})
                for index, i in enumerate(other_news.find_all('div', {'class', 'article_content_text'})):
                    news_date = datetime.strptime(newsheader[index].span['title'][0:8], "%d.%m.%y").date()
                    news_title = newsheader[index].text.split(">")[1].strip()
                    if news_date < until_date:
                        more_news = None
                        break
                    self.news.append([news_date, news_title, i.text])
                first_news += 10
                time.sleep(1)
        return self.news

    def players_onsale(self):
        """
        Returns the football players currently on sale
        @return: [[name, team, min_price, market_price, points, date, owner, position]]
        :param only_computer:
        :param community_id:
        """
        headers.update({'Referer': self.urls['news']})
        req = self.session.get(self.urls['team'], headers=headers).content
        soup = BeautifulSoup(req, "html.parser")

        current_year = dt.today().year
        current_month = dt.today().month
        on_sale = list()
        year_flag = 0
        for i in soup.find_all('table', {'class', 'tablecontent03'})[2].find_all('tr')[1:]:
            columns = i.find_all('td')
            player_id = int(re.findall('\d+', columns[0].img['src'])[0])
            playername = columns[1].text.strip()
            team_id = int(re.findall('\d+', columns[2].img['src'])[0])
            team = columns[2].a['title'].strip()
            min_price = float(columns[3].text.replace(".", "").strip())
            market_price = float(columns[4].text.replace(".", "").strip())
            points = int(columns[5].text.strip().strip())
            # Controls the change of year
            if current_month <= 7 < int(columns[6].text[3:5]):
                year_flag = 1

            current_date = str(current_year - year_flag) + columns[6].text[3:5] + columns[6].text[:2]
            date = datetime.strptime(current_date, '%Y%m%d').date()
            owner = columns[7].text.strip()
            position = self.translate_position(columns[8].text.strip())
            on_sale.append(
                [player_id, playername, team_id, team, min_price, market_price, points, date, owner, position])

        return on_sale

    @staticmethod
    def get_money_bids(username):
        url_comuniazo = 'http://www.comuniazo.com'
        headers_zo = {'Accept': '*/*', 'Referer': url_comuniazo + '/comunio/dinero',
                      'Host': 'www.comuniazo.com', 'X-Requested-With': 'XMLHttpRequest'}

        ses = requests.session()
        ses.get(url_comuniazo + '/comunio/dinero', headers=headers_zo)
        money_html = ses.get(url_comuniazo + '/ajax/dinero.php?user=%s&dinero=20000000' % username,
                             headers=headers_zo).content
        money_bids = json.loads(money_html)

        return money_bids

    @staticmethod
    def translate_position(position):
        positions = {'Portero': 'Goalkeeper', 'Defensa': 'Defender', 'Centrocampista': 'Midfielder',
                     'Delantero': 'Striker'}
        return positions.get(position, position)

    @staticmethod
    def translate_dates(dates):
        """
        Translates dates format from 'xx de Month' or 'dd.mm' to date('yyyy-mm-dd')
        :param dates: Array dates from Comuniazo or Comunio.
        :return: [[date,]]
        """
        formatted_dates = list()
        year = dt.today().year
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
                year -= 1

            p_date = datetime.strptime('%s%s%s' % (year, month, day), "%Y%m%d").date()
            formatted_dates.append(p_date)
        return formatted_dates

    @staticmethod
    def check_exceptions(playername):
        """
        Fix exceptions for a player name between Comunio and Comuniazo.
        :param playername: Name of the football player.
        :return: Corrected name.
        """
        exceptions = {'Banega': 'Ever Banega', 'Mikel': u'Mikel González', u'Isma López': u'Ismael López'}
        return exceptions.get(playername, playername)
