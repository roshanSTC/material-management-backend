"""update_purchase_orders_and_items_schema

Revision ID: ea3c148f0567
Revises: 4adfd82718ae
Create Date: 2026-09-07 12:01:55.569087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea3c148f0567'
down_revision = '4adfd82718ae'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('purchase_order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('material_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('net_amount', sa.Numeric(precision=18, scale=2), nullable=True))

    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.alter_column('gst', new_column_name='gst_rate')
        batch_op.add_column(sa.Column('gst_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('total_net_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('total_gross_amount', sa.Numeric(precision=18, scale=2), nullable=True))


def downgrade():
    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.drop_column('total_gross_amount')
        batch_op.drop_column('total_net_amount')
        batch_op.drop_column('gst_amount')
        batch_op.alter_column('gst_rate', new_column_name='gst')

    with op.batch_alter_table('purchase_order_items', schema=None) as batch_op:
        batch_op.drop_column('net_amount')
        batch_op.drop_column('material_name')

