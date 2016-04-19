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

    prc_price = list()
    for player in user.players:
        t = Transaction.query.filter_by(player_id=player.id).filter_by(user_id=user.id).filter_by(sort='Buy').order_by(Transaction.date.desc()).first()
        if t:
            prc_price.append(t.price)
        else:
            min_date = Transaction.query.order_by(Transaction.date.desc()).first().date
            diff_days = (min_date - date.today()).days
            prc_price.append(player.prices[-diff_days].price)

    return render_template('sell.html', username=session.get('username'), user=user, prc_price=prc_price, submenu='Players to Sell')


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
