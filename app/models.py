from . import db


class Club(db.Model):
    __tablename__ = 'clubs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)

    def __repr__(self):
        return 'User %r' % self.name


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(64))
    position = db.Column(db.String(64))
    club = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=True)

    def __repr__(self):
        return 'Name %r, Position %r, Club %r' % (self.name, self.position, self.club)


class Points(db.Model):
    __tablename__ = 'points'
    id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    gameday = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'Points %r' % self.points


class Price(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    price = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'Price %r' % self.price


class Transaction(db.Model):
    __tablename__ = 'transactions'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    sort = db.Column(db.String(64), doc='Buy/Sell')
    price = db.Column(db.Integer)
    date = db.Column(db.Date, primary_key=True)

    def __repr__(self):
        return 'Transaction %r' % self.player_id


class Userdata(db.Model):
    __tablename__ = 'usersdata'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    points = db.Column(db.Integer, nullable=False)
    money = db.Column(db.Integer, nullable=False)
    teamvalue = db.Column(db.Integer, nullable=False)
    maxbid = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'Userdata %r' % self.points


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), primary_key=True)
    players = db.relationship('Player',
                            backref=db.backref('user', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')

    userdata = db.relationship('Userdata', foreign_keys=[Userdata.id], lazy='dynamic')
    transactions = db.relationship('Transaction', lazy='dynamic')

    def __repr__(self):
        return 'Name %r, Players %r, Userdata %r, Transactions %r' % (self.name, self.players, self.userdata, self.transactions)


