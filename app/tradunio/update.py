#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on April 11, 2016
@author: jotacor
"""

from app import db
from ComunioPy import Comunio
from datetime import date, timedelta
from ..models import User, Userdata, Transaction, Player, Club, Price, Points
import re

def update(login, passwd):
    """
    Update the database with new data.
    """
    db.create_all()
    com = Comunio(login, passwd, 'BBVA')
    users = set_users_data(com)

    for user in users:
        players = set_user_players(com, user)
        for player in players:
            if player.club_id == 25:
                # Player is not in Primera División
                continue
            set_player_data(com, player_id=player.id, playername=player.name)

    set_transactions(com)


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


def set_player_data(com, player_id=None, playername=None):
    """
    Sets prices and points for all the players of the user
    :param player_id: Id of the football player
    :param playername: Football player name
    :return: Players of the user id
    """
    days_left = days_wo_price(player_id)
    prices, points = list(), list()
    if days_left:
        dates, prices, points_all = com.get_player_data(playername=playername)
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
            if not Points.query.filter_by(id=player.id).filter_by(gameday=gameday).first():
                pt = Points(id=player.id, gameday=gameday, points=points)
                db.session.add(pt)

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
                player = db.session.query(Player).filter(Player.name.like('%'+playername+'%')).first()
                if 'Computer' in fr:
                    kind = 'Buy'
                    user = db.session.query(User).filter(User.name.like('%' + to + '%')).first()
                    t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                    db.session.add(t)
                elif 'Computer' in to:
                    kind = 'Sell'
                    user = db.session.query(User).filter(User.name.like('%' + fr + '%')).first()
                    t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                    db.session.add(t)
                else:
                    kind = 'Buy'
                    user = db.session.query(User).filter(User.name.like('%' + to + '%')).first()
                    t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                    db.session.add(t)

                    user = db.session.query(User).filter(User.name.like('%' + fr + '%')).first()
                    kind = 'Sell'
                    t = Transaction(player_id=player.id, user_id=user.id, sort=kind, price=value, date=ndate)
                    db.session.add(t)

                db.session.commit()

            except IndexError:
                # Player selled before having in database
                pass


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
    :param team_id:
    """
    c = Club.query.filter_by(id=club_id)
    p = Player(id=player_id, name=playername, position=position, club=c)
    db.session.add(p)
    db.session.commit()
    return p


