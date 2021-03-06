"""added username to User

Revision ID: 2a240390d131
Revises: 371a23dc978c
Create Date: 2016-04-14 00:50:05.084303

"""

# revision identifiers, used by Alembic.
revision = '2a240390d131'
down_revision = '371a23dc978c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('username', sa.String(length=64), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'username')
    ### end Alembic commands ###
