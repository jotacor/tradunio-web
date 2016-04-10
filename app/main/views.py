from flask import render_template, session, redirect, url_for, current_app
from .. import db
from ..models import User
from ..email import send_email
from . import main
from .forms import NameForm


@main.route('/', methods=['GET', 'POST'])
def index():
    if session.get('username', None):
        return redirect(url_for('.menu'))

    form = NameForm()
    if form.validate_on_submit():
        session['username'] = form.username.data
        session['password'] = form.password.data

        if current_app.config['TRADUNIO_ADMIN']:
            send_email(current_app.config['TRADUNIO_ADMIN'], 'New Login',
                       'mail/new_user', user=session.get('username'))

        return redirect(url_for('.menu'))

    return render_template('index.html', form=form)


@main.route('/menu', methods=['GET'])
def menu():
    if not session.get('username', None):
        return redirect(url_for('.index'))

    return render_template('menu.html', username=session.get('username'),
                           players=[[1, 2, 3, 4, 5, 6, 7], [11, 12, 13, 14, 15, 16, 17]])


@main.route('/sell', methods=['GET'])
def sell():
    if not session.get('username', None):
        return redirect(url_for('.index'))

    return render_template('menu.html', username=session.get('username'),
                           submenu='Players to Sell', function='sell',
                           players=[[1,2,3,4,5,6,7,8,9,10], [11,12,13,14,15,16,17,18,19,20]])


@main.route('/buy', methods=['GET'])
def buy():
    if not session.get('username', None):
        return redirect(url_for('.index'))

    return render_template('menu.html', username=session.get('username'),
                           submenu='Players to Buy', function='buy',
                           players=[[10,9,8,7,6,5,4,3,2,1], [20,19,18,17,16,15,14,13,12,11]])


@main.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('.index'))


@main.route('/update', methods=['GET'])
def update():
    if not session.get('username', None):
        return redirect(url_for('.index'))

    return render_template('menu.html', username=session.get('username'))