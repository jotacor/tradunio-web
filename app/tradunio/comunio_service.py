#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup as bs
from datetime import date, timedelta, datetime
import re
from suds.client import Client


class Comunio:
    def __init__(self):
        self.client = Client(url='http://www.comunio.es/soapservice.php?wsdl')
        self.today = date.today()

    def get_player_price(self, playerid, from_date=None):
        if from_date:
            prices = list()
            loop_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            while loop_date <= self.today:
                price = self.client.service.getquote(playerid=playerid, date=loop_date)
                prices.append([loop_date, price])
                loop_date = loop_date + timedelta(days=1)
        else:
            price = self.client.service.getquote(playerid=playerid, date=self.today)
            prices = [self.today, price]

        return prices

    def get_clubs(self):
        clubs_comunio = self.client.service.getclubs()
        clubs = list()
        for club in clubs_comunio:
            club_id = club.id[0]
            club_name = club.name[0].encode('utf-8')
            clubs.append([club_id, club_name])

        return clubs

    def get_playersbyclubid(self, club_id=None):
        players_comunio, players_list = list(), list()
        if not club_id:
            clubs = self.get_clubs()
            for club in clubs:
                club_id, clubname = club
                players_comunio.append(self.client.service.getplayersbyclubid(club_id))
        else:
            players_comunio.append(self.client.service.getplayersbyclubid(club_id))

        for club_players in players_comunio:
            for player in club_players:
                players_list.append([
                    player.id[0],
                    player.name[0].encode('utf-8').strip(),
                    player.points[0],
                    player.clubid[0],
                    player.quote[0],
                    player.status[0].encode('utf-8'),
                    player.status_info[0].encode('utf-8') if player.status_info else None,
                    player.position[0].encode('utf-8'),
                    player.rankedgamesnumber[0]
                ])

        return players_list

    def get_market(self, community_id=None, user_id=None):
        """
        Get the market from the community_id or the user_id
        :param community_id:
        :param user_id:
        :return: [player_id, playername, points, club_id, market_price, min_price, status, injured, position, placed_date, owner_id]
        """
        if not community_id:
            community_id = self.client.service.getcommunityid(user_id)

        market_comunio = self.client.service.getcommunitymarket(community_id)
        market = list()
        for listed in market_comunio:
            market.append([
                listed.id[0],
                listed.name[0].encode('utf-8').strip(),
                listed.points[0],
                listed.clubid[0],
                listed.quote[0],
                listed.recommendedprice[0],
                listed.status[0].encode('utf-8'),
                listed.status_info[0].encode('utf-8') if listed.status_info else None,
                listed.position[0].encode('utf-8'),
                listed.placed[0],
                listed.ownerid[0],
            ])

        return market

    def get_transactions(self, community_id=None, user_id=None):
        if not community_id:
            community_id = self.client.service.getcommunityid(user_id)

        news_comunio = self.client.service.getcomputernews(community_id, 30, 30)
        transactions = list()
        pattern = re.compile(
            ur'(?:(?:\\n)?([(\S+ )]+?)(?: cambia por )([0-9\.,]*?)(?: .*? de )(.+?) a (.+?)\.)', re.UNICODE)
        for published in news_comunio:
            if published.subject[0] == 'Fichajes':
                message = bs(published.message[0].encode('utf-8'), "html.parser")
                player_id = int(re.findall('\d+', message.a['href'])[0])
                trans = re.findall(pattern, message.text)[0]
                playername, value, fr, to = trans
                transactions.append([
                    datetime.strptime(published.date[0][0:10], '%Y-%m-%d').date(),
                    player_id, playername, int(value.replace('.', '')), fr, to
                ])

        return transactions

    def get_gamedays(self):
        gamedays_comunio = self.client.service.getgamedays()
        gamedays_list = list()
        for gamedays in gamedays_comunio:
            gameday_id = int(gamedays[0][0].value[0])
            number = int(gamedays[0][1].value[0])
            gamedate = datetime.strptime(gamedays[0][3].value[0][0:10], '%Y-%m-%d').date()
            shifted = bool(gamedays[0][4].value[0])
            gamedays_list.append([number, gameday_id, gamedate, shifted])

        return gamedays_list



# c = Comunio()
# print c.get_player_price(3, '2016-05-01')
# print c.get_clubs()
# print c.get_market(user_id=15797714)
# a=c.get_transactions(user_id=15797714)
# print c.get_playersbyclubid(15)
# print c.get_gamedays()
# pass
