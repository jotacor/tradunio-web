#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import date as dt
from datetime import datetime
import json
import re
import requests


class Comuniazo:
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) ' \
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102'
        self.headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        self.url_comuniazo = 'http://www.comuniazo.com'
        self.session = requests.session()

    def get_player_data(self, playername=None):
        """
        Get historical prices from a player from Comuniazo
        :param playername: Name of the player.
        :return: [dates], [prices], [gameday, points]
        """
        self.headers.update({'Referer': self.url_comuniazo})
        url_jugadores = self.url_comuniazo + '/comunio/jugadores/'
        suffix, lastname = '', ''
        count = 0
        dates, points, prices = list(), list(), list()
        while True and len(dates) < 2:
            playername = Comuniazo.check_exceptions(playername)
            url_playername = re.sub("['.]", "", playername).replace(" ", "-")
            req = self.session.get(url_jugadores + url_playername + suffix, headers=self.headers).content
            dates_re = re.search("(\"[0-9 ][0-9] de \w+\",?,?)+", req)
            season_re = re.search("[0-9][0-9]_[0-9][0-9]", req)
            try:
                dates = dates_re.group(0).replace('"', '').split(",")
                dates = Comuniazo.translate_dates(dates)
                season = season_re.group(0)
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
                raise AttributeError

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
                        points.append([season, gameday, int(row.div.text)])
                    else:
                        points.append([season, gameday, 0])
            except AttributeError:
                # Player without points
                pass

            if suffix == '-2' or len(dates) > 2:
                break
            else:
                suffix = '-2'

        return dates, prices, points

    def get_money_bids(self, username, money=20000000):
        headers = {'Accept': '*/*', 'Referer': self.url_comuniazo + '/comunio/dinero',
                   'Host': 'www.comuniazo.com', 'X-Requested-With': 'XMLHttpRequest'}

        self.session.get(self.url_comuniazo + '/comunio/dinero', headers=headers)
        money_html = self.session.get(self.url_comuniazo + '/ajax/dinero.php?user=%s&dinero=%s' % (username, money),
                                      headers=headers).content
        money_bids = json.loads(money_html)

        return money_bids

    @staticmethod
    def translate_dates(dates):
        """
        Translates dates format from 'xx de Month' or 'dd.mm' to date('yyyy-mm-dd')
        :param dates: Array dates from Comuniazo or Comunio.
        :return: [[date],]
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
