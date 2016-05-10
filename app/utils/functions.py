def user_to_dict(user):
    ud = user.userdata[-1]
    return dict(date=ud.date, teamvalue=ud.teamvalue, money=ud.money, maxbid=ud.maxbid,
                totalpoints=ud.points, num_players=user.players.count())
