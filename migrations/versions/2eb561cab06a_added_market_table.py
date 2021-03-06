"""Added Market table



Revision ID: 2eb561cab06a

Revises: 2a240390d131

Create Date: 2016-05-10 12:40:08.397000



"""



# revision identifiers, used by Alembic.

revision = '2eb561cab06a'

down_revision = '2a240390d131'



from alembic import op

import sqlalchemy as sa





def upgrade():

    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('market',
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('mkt_price', sa.Integer(), nullable=True),
    sa.Column('min_price', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], ),
    sa.PrimaryKeyConstraint('owner_id', 'player_id', 'date')
    )
    ### end Alembic commands ###





def downgrade():

    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('market')
    ### end Alembic commands ###

