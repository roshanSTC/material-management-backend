"""add currency_unit to supplier_order_confirmations

Revision ID: a1b2c3d4e5f6
Revises: f9a1b2c3d4e5
Create Date: 2026-09-28 13:11:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f9a1b2c3d4e5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('supplier_order_confirmations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency_unit', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('supplier_order_confirmations', schema=None) as batch_op:
        batch_op.drop_column('currency_unit')
