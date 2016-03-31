import unittest
from app.models import User, Club, Player, Points, Price, Transaction, Userdata
from app import create_app, db
from datetime import date, timedelta


class DataCreationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_data_creation(self):
        c = Club(id=5, name='Test')
        p = Player(id=7, name='Potato', position='Alante', club=c)
        u = User(id=3, name='Yo', players=[p])

        ud = Userdata(id=u, date=date.today(), points=12, money=14, teamvalue=111, maxbid=12331)
        t = Transaction(player_id=p.id, user_id=u.id, sort="Sell", price = 123, date = date.today())
        u.userdata.append(ud)
        u.transactions.append(t)

        pt = Points(id=p, gameday=1, points=10)
        ptt = Points(id=p, gameday=2, points=6)
        pr = Price(id=p, date=date.today(), price=160000)
        prr = Price(id=p, date=date.today() + timedelta(days=1), price=200000)
        p.prices.extend([pr, prr])
        p.points.extend([pt, ptt])

        # db.session.add_all([u, c, p, ud, t, pt, ptt, pr, prr])
        db.session.add(u)
        db.session.commit()

        u = User.query.filter_by(id=3).first()
        self.assertTrue(u.name == 'Yo')
        self.assertEqual(u.players.count(), 1)
        self.assertEqual(u.players[0].prices.count(), 2)
