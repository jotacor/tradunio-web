"""Added Owner and Community classes

Revision ID: 549e55d55f1

Revises: 2eb561cab06a

Create Date: 2016-05-26 14:50:49.133000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app import db

#  revision identifiers, used by Alembic.
revision = '549e55d55f1'
down_revision = '2eb561cab06a'

Base = declarative_base()


class Owner(Base):
    __tablename__ = 'owners'
    player_id = sa.Column(sa.Integer, sa.ForeignKey('players.id'), primary_key=True)
    owner_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), primary_key=True)


class Player(Base):
    __tablename__ = 'players'
    id = sa.Column(sa.Integer, primary_key=True)
    owner = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=True)


class User(Base):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('communities',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=64), nullable=False),
                    sa.PrimaryKeyConstraint('id', 'name')
                    )
    op.create_table('owners',
                    sa.Column('player_id', sa.Integer(), nullable=False),
                    sa.Column('owner_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
                    sa.PrimaryKeyConstraint('player_id', 'owner_id')
                    )
    op.add_column(u'users', sa.Column('community_id', sa.Integer(), nullable=True))

    for player_id, owner_id in db.session.query(Player.id, Player.owner).distinct():
        if not player_id or not owner_id:
            continue
        db.session.add(Owner(player_id=player_id, owner_id=owner_id))
        db.session.commit()

    drop_column_sqlite('players', 'owner')

    # op.drop_column(u'players', 'owner') # it fails in sqlite because it is not allowed
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'users', 'community_id')
    op.add_column(u'players', sa.Column('owner', sa.INTEGER(), nullable=True))
    op.drop_table('owners')
    op.drop_table('communities')
    ### end Alembic commands ###


def drop_column_sqlite(tablename, columns):
    """ column dropping functionality for SQLite """

    from copy import copy
    # get the db engine and reflect database tables
    engine = op.get_bind()
    meta = sa.MetaData(bind=engine)
    meta.reflect()

    # create a select statement from the old table
    old_table = meta.tables[tablename]
    select = sa.sql.select([c for c in old_table.c if c.name not in columns])

    # get remaining columns without table attribute attached
    remaining_columns = [copy(c) for c in old_table.columns
                         if c.name not in columns]
    for column in remaining_columns:
        column.table = None

    # create a temporary new table
    new_tablename = '{0}_new'.format(tablename)
    op.create_table(new_tablename, *remaining_columns)
    meta.reflect()
    new_table = meta.tables[new_tablename]

    # copy data from old table
    insert = sa.sql.insert(new_table).from_select(
        [c.name for c in remaining_columns], select)
    engine.execute(insert)

    # drop the old table and rename the new table to take the old tables
    # position
    op.drop_table(tablename)
    op.rename_table(new_tablename, tablename)
