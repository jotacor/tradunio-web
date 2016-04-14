#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Club, Player, Points, Price, Transaction, Userdata
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app.tradunio.update import update as tradunio_update

app = create_app(os.getenv('TRADUNIO_ENV') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Club=Club, Player=Player,
                Points=Points, Price=Price, Transaction=Transaction, Userdata=Userdata)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.option('-l', '--login', dest='login', default=None)
@manager.option('-p', '--passwd', dest='passwd', default=None)
def update(login, passwd):
    """ Updates the database with new data from Comunio. """
    if login is None or passwd is None:
        print ("Give me login and password of Comunio to update the database.")
        exit(1)
    tradunio_update(login, passwd)


@manager.command
def test():
    """ Run the unit tests. """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.template_filter()
def sum_points(points):
    total_points = 0
    for point in points:
        total_points += point.points
    return total_points


@app.template_filter()
def format_money(money):
    return u"{:,.0f}\u20AC".format(money)


if __name__ == '__main__':
    manager.run()
