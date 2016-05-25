#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup as bs
from datetime import date, timedelta, datetime
from suds.client import Client

class Comunio():
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

    def get_market(self, community_id=None, user_id=None):
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
                listed.status_info,
                listed.position[0].encode('utf-8'),
                listed.placed[0],
                listed.ownerid[0],
            ])

        return market

    def get_signings(self, community_id=None, user_id=None):
        if not community_id:
            community_id = self.client.service.getcommunityid(user_id)

        news_comunio = self.client.service.getcomputernews(community_id, 30, 30)
        news = list()
        for published in news_comunio:
            if published.subject[0] == 'Fichajes':
                message = bs(published.message[0].encode('utf-8'))
                message.a
                message.text
                news.append([
                    published.date[0],
                    published.author[0],
                    published.subject[0],
                    published.message[0].encode('utf-8'),
                ])

        return news


c = Comunio()
#print c.get_player_price(3, '2016-05-01')
#print c.get_clubs()
#print c.get_market(user_id=15797714)
print c.get_signings(user_id=15797714)
pass
