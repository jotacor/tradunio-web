def user_to_dict(user):
    ud = user.userdata[-1]
    return dict(date=ud.date, teamvalue=ud.teamvalue, money=ud.money, maxbid=ud.maxbid,
                totalpoints=ud.points, num_players=user.players.count())


def get_week_month_prices(prices):
    prices_length = prices.count()
    if prices_length >= 30:
        month_price = prices[-30].price
        week_price = prices[-8].price
    elif prices_length >= 8:
        month_price = prices[-prices_length].price
        week_price = prices[-8].price
    else:
        month_price = prices[-prices_length].price
        week_price = prices[-prices_length].price

    return month_price, week_price
