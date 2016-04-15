from . import utils


@utils.app_template_filter()
def format_money(money):
    return u"{:,.0f}\u20AC".format(money)


@utils.app_template_filter()
def sum_points(points):
    total_points = 0
    for point in points:
        total_points += point.points
    return total_points
