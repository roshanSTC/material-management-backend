"""add gst_rate gst_amount round_off net_total to delivery_challans

Revision ID: 70dfdde4a82b
Revises: c6e80a23bf93
Create Date: 2026-09-10 17:55:33.535244

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70dfdde4a82b'
down_revision = 'c6e80a23bf93'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('delivery_challans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gst_rate', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('gst_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('round_off', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('net_total', sa.Numeric(precision=18, scale=2), nullable=True))


def downgrade():
    with op.batch_alter_table('delivery_challans', schema=None) as batch_op:
        batch_op.drop_column('net_total')
        batch_op.drop_column('round_off')
        batch_op.drop_column('gst_amount')
        batch_op.drop_column('gst_rate')
