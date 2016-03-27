from . import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), primary_key=True)
    #players_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    #userdata_id = db.Column(db.Integer, db.ForeignKey('userdata.id'))
    #transactions_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    playername = db.Column(db.String(64))
    position = db.Column(db.String(64))
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=True)

    def __repr__(self):
        return '<Player %r>' % self.playername


class Club(db.Model):
    __tablename__ = 'clubs'
    id = db.Column(db.Integer, primary_key=True)
    clubname = db.Column(db.String(64), unique=True, index=True)

    def __repr__(self):
        return '<Clubs %r>' % self.clubname


class Owner(db.Model):
    __tablename__ = 'owners'
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Points(db.Model):
    __tablename__ = 'points'
    id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    gameday = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Points %r>' % self.points


class Price(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    price = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Price %r>' % self.points


class Transaction(db.Model):
    __tablename__ = 'transactions'
    idp = db.Column(db.Integer, db.ForeignKey('players.id'), primary_key=True)
    idu = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    type = db.Column(db.String(64), doc='Buy/Sell')
    price = db.Column(db.Integer)
    date = db.Column(db.Date, primary_key=True)


#class Role(db.Model):
#    __tablename__ = 'roles'
#    id = db.Column(db.Integer, primary_key=True)
#    name = db.Column(db.String(64), unique=True)
#    users = db.relationship('User', backref='role', lazy='dynamic')
#
#    def __repr__(self):
#        return '<Role %r>' % self.name


