from flask import render_template, session, redirect, url_for, current_app
from .. import db
from ..models import User, Transaction, Market, Player
from ..email import send_email
from . import main
from .forms import NameForm
from ..tradunio.update import update_market
from ..utils.functions import user_to_dict, get_week_month_prices
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

    players = list()
    for player in user.players:
        total_points = sum(point.points for point in player.points)

        players.append({'name': player.name, 'position': player.position, 'clubname': player.club.name,
                        'today': player.prices[-1].price, 'last_points': player.points[-5:], 'total_points': total_points})

    user = user_to_dict(user)
    return render_template('index.html', username=session.get('username'), user=user, players=players)


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

        month_price, week_price = get_week_month_prices(player.prices)

        players.append({'name': player.name, 'position':player.position, 'month': month_price, 'week': week_price,
                        'day': player.prices[-2].price, 'today':player.prices[-1].price, 'last_points':player.points[-5:], 'prc_price': prc_price })

    user = user_to_dict(user)
    return render_template('sell.html', username=session.get('username'), players=players, user=user, submenu='Players to Sell')


@main.route('/buy', methods=['GET'])
def buy():
    if not session.get('username', None):
        return redirect(url_for('.login'))

    user = User.query.filter_by(username=session.get('username')).first()
    if not user:
        return redirect(url_for('.logout'))

    on_sale = Market.query.filter_by(date=date.today()).all()

    players = list()
    for player in on_sale:
        p = Player.query.filter_by(id=player.player_id).first()
        owner = User.query.filter_by(id=player.owner_id).first().name

        month_price, week_price = get_week_month_prices(p.prices)

        players.append({'name': p.name, 'position': p.position, 'clubname': p.club.name, 'today': player.mkt_price,
                        'min_price': player.min_price, 'last_points': p.points[-5:], 'owner': owner,
                        'month': month_price, 'week': week_price, 'day': p.prices[-2].price
                         })

    user = user_to_dict(user)
    return render_template('buy.html', username=session.get('username'), user=user, players=players, submenu='Players to Buy')


@main.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('.login'))


@main.route('/update_mkt', methods=['GET'])
def update_mkt():
    if not session.get('username', None):
        return redirect(url_for('.login'))

    update_market(session.get('username'), session.get('password'))
    return redirect(url_for('.buy'))


# def user_to_dict(user):
#     ud = user.userdata[-1]
#     return dict(date=ud.date, teamvalue=ud.teamvalue, money=ud.money, maxbid=ud.maxbid,
#                 totalpoints=ud.points, num_players=user.players.count())
