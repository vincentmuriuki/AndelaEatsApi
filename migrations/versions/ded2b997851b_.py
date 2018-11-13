"""empty message

Revision ID: ded2b997851b
Revises: d4d103b1f9bb
Create Date: 2018-11-13 11:08:16.196228

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ded2b997851b'
down_revision = 'd4d103b1f9bb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('meal_period', sa.Enum('lunch', 'breakfast', name='mealperiods'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'meal_period')
    # ### end Alembic commands ###