"""Add price field to Event model

Revision ID: 96877cdf898a
Revises: 
Create Date: 2023-12-13 07:26:18.264757

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96877cdf898a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.add_column(sa.Column('price', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('event', schema=None) as batch_op:
        batch_op.drop_column('price')

    # ### end Alembic commands ###
