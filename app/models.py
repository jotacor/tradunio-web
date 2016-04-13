from . import db


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=True)
    name = db.Column(db.String(64))
    position = db.Column(db.String(64))
    prices = db.relationship('Price', lazy='dynamic', order_by='Price.date')
    points = db.relationship('Points', lazy='dynamic', order_by='Points.gameday')

    def __repr__(self):
        return 'Name: %r, Position: %r, Club: %r, Points: %r, Price: %r' \
               % (self.name, self.position, self.club.name, sum(p.points for p in self.points),
                  self.prices[-1].price)


class Club(db.Model):
    __tablename__ = 'clubs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    players = db.relationship('Player', foreign_keys=[Player.club_id],
                              backref=db.backref('club', lazy='joined'),
                              lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return 'Club: %r' % self.name


class Points(db.Model):
    __tablename__ = 'points'
    id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    gameday = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'Points: %r' % self.points


class Price(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    price = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'Price: %r' % self.price


class Transaction(db.Model):
    __tablename__ = 'transactions'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    sort = db.Column(db.String(64), doc='Buy/Sell')
    price = db.Column(db.Integer)

    def __repr__(self):
        return 'Transaction: %r %r - %r => %r (%r)' % (self.date, self.sort, self.player_id, self.user_id, self.price)


class Userdata(db.Model):
    __tablename__ = 'usersdata'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    points = db.Column(db.Integer, nullable=False)
    money = db.Column(db.Integer, nullable=False)
    teamvalue = db.Column(db.Integer, nullable=False)
    maxbid = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return 'Userdata: %r' % self.points


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(64))
    players = db.relationship('Player', backref=db.backref('user', lazy='joined'),
                              lazy='dynamic', cascade='all, delete-orphan')
    userdata = db.relationship('Userdata', foreign_keys=[Userdata.id], lazy='dynamic', order_by='Userdata.date')
    transactions = db.relationship('Transaction', foreign_keys=[Transaction.user_id], lazy='dynamic', order_by='Transaction.date')

    def __repr__(self):
        return 'Name %r, Players %r, Userdata %r, Transactions %r' \
               % (self.name, self.players, self.userdata, self.transactions)


