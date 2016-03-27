from . import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    players_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    userdata_id = db.Column(db.Integer, db.ForeignKey('userdata.id'))
    transactions_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))

    def __repr__(self):
        return '<User %r>' % self.username


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    playername = db.Column(db.String(64), unique=True, index=True)
    position = db.Column(db.String(64))
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'))

    def __repr__(self):
        return '<Player %r>' % self.playername


class Club(db.Model):
    __tablename__ = 'clubs'
    id = db.Column(db.Integer, primary_key=True)
    clubname = db.Column(db.String(64), unique=True, index=True)

    def __repr__(self):
        return '<Clubs %r>' % self.playername


class Owner(db.Model):
    __tablename__ = 'owners'
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Points(db.Model):
    __tablename__ = 'points'
    id = db.Column(db.Integer, primary_key=True)
    gameday = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Integer)

    def __repr__(self):
        return '<Gamedays %r>' % self.gameday


# TODO: prices and the rest


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


