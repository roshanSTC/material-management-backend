"""add value_symbol to supplier_quotations and unit_price, net_amount to supplier_quotation_items

Revision ID: c49a6283d1b8
Revises: e7b2f4c91a85
Create Date: 2026-09-03 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c49a6283d1b8'
down_revision = 'e7b2f4c91a85'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('supplier_quotations', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('value_symbol', sa.String(length=20), nullable=True)
        )

    with op.batch_alter_table('supplier_quotation_items', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('unit_price', sa.Numeric(precision=18, scale=2), nullable=True)
        )
        batch_op.add_column(
            sa.Column('net_amount', sa.Numeric(precision=18, scale=2), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('supplier_quotation_items', schema=None) as batch_op:
        batch_op.drop_column('net_amount')
        batch_op.drop_column('unit_price')

    with op.batch_alter_table('supplier_quotations', schema=None) as batch_op:
        batch_op.drop_column('value_symbol')

