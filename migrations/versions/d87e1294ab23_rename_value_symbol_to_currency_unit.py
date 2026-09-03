"""rename value_symbol to currency_unit on supplier_quotations

Revision ID: d87e1294ab23
Revises: c49a6283d1b8
Create Date: 2026-09-03 12:26:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd87e1294ab23'
down_revision = 'c49a6283d1b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('supplier_quotations', schema=None) as batch_op:
        batch_op.alter_column('value_symbol', new_column_name='currency_unit')


def downgrade():
    with op.batch_alter_table('supplier_quotations', schema=None) as batch_op:
        batch_op.alter_column('currency_unit', new_column_name='value_symbol')

