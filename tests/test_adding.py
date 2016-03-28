"""

c=Club(id=1, name='Test')
p=Player(id=1, name='Potato', position='Alante', club=c)
ud=Userdata(id=1, date=date.today(), points=12, money=14, teamvalue=111, maxbid=12331)
u=User(name='Yo', players=[p], userdata=[ud])
t=Transaction(player_id=p, user_id=u, sort=“Sell”, price=123, date=date.today())

"""