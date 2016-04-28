from flask import render_template, session, redirect, url_for, current_app
from .. import db
from ..models import User, Transaction
from ..email import send_email
from . import main
from .forms import NameForm
from ..tradunio.update import update as tradunio_update
from datetime import date


@main.route('/', methods=['GET', 'POST'])
def login():
    db.create_all()
    if session.get('username', None):
        return redirect(url_for('.index'))

    form = NameForm()
    if form.validate_on_submit():
        session['username'] = form.username.data
        session['password'] = form.password.data

        # if current_app.config['TRADUNIO_ADMIN']:
        #     send_email(current_app.config['TRADUNIO_ADMIN'], 'New Login',
        #                'mail/new_user', user=session.get('username'))

        return redirect(url_for('.index'))

    return render_template('login.html', form=form)


@main.route('/index', methods=['GET'])
def index():
    if not session.get('username', None):
        return redirect(url_for('.login'))

    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        return redirect(url_for('.logout'))

    return render_template('index.html', username=session.get('username'), user=user)


@main.route('/sell', methods=['GET'])
def sell():
    if not session.get('username', None):
        return redirect(url_for('.login'))

    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        return redirect(url_for('.logout'))

    players = list()
    for player in user.players:
        t = Transaction.query.filter_by(player_id=player.id).filter_by(user_id=user.id).filter_by(sort='Buy').order_by(Transaction.date.desc()).first()
        if t:
            prc_price = t.price
        else:
            min_date = Transaction.query.order_by(Transaction.date.desc()).first().date
            diff_days = (min_date - date.today()).days
            prc_price = player.prices[-diff_days].price

        players.append({'name': player.name, 'position':player.position, 'month': player.prices[-30].price, 'week': player.prices[-8].price,
                        'day': player.prices[-2].price, 'today':player.prices[-1].price, 'last_points':player.points[-5:], 'prc_price': prc_price })

    return render_template('sell.html', username=session.get('username'), players = players, user=user, submenu='Players to Sell')


@main.route('/buy', methods=['GET'])
def buy():
    if not session.get('username', None):
        return redirect(url_for('.login'))

    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        return redirect(url_for('.logout'))

    return render_template('buy.html', username=session.get('username'), user=user, submenu='Players to Buy')


@main.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('.login'))


@main.route('/update', methods=['GET'])
def update():
    if not session.get('username', None):
        return redirect(url_for('.login'))

    tradunio_update(session.get('username'), session.get('password'))

    return render_template('index.html', username=session.get('username'))
