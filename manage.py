#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Club, Player, Points, Price, Transaction, Userdata
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('TRADUNIO_ENV') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Club=Club, Player=Player,
                Points=Points, Price=Price, Transaction=Transaction, Userdata=Userdata)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """ Run the unit tests. """
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()