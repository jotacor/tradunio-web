from . import utils


@utils.app_template_filter()
def format_money(money):
    if not isinstance(money, (int, long)):
        money = 0
    return u"{:,.0f}\u20AC".format(money)


@utils.app_template_filter()
def sum_points(points):
    total_points = 0
    for point in points:
        total_points += point.points
    return total_points


@utils.app_template_filter()
def format_gamedays(gamedays):
    result = ''
    for points in gamedays:
        color = {
            points.points < 0: 'danger',
            points.points == 0: 'default',
            0 < points.points <= 2: 'warning',
            2 < points.points < 10: 'success',
            10 <= points.points < 9999: 'primary'
        }
        result += '<span class="label-%s last-points">%s</span>' % (color[True], points.points)
    return result


@utils.app_template_filter()
def profit(price_ago, mkt_price):
    if not price_ago or not mkt_price:
        prof = 0
    else:
        prof = (mkt_price - price_ago) / float(price_ago) * 100

    color = {
        prof <= -10: 'danger',
        -10 < prof <= 0: 'warning',
        0 < prof < 10: 'success',
        10 <= prof < 9999: 'primary'
    }
    return '<span class="label-%s profit">%4d%%</span>' % (color[True], prof)
