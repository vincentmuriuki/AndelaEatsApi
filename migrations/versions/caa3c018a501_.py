"""empty message

Revision ID: caa3c018a501
Revises: 3b0e02472118
Create Date: 2018-11-26 16:11:39.479499

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'caa3c018a501'
down_revision = '3b0e02472118'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('has_rated', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'has_rated')
    # ### end Alembic commands ###
