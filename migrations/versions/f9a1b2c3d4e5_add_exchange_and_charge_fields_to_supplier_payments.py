"""add exchange and charge fields to supplier payments

Revision ID: f9a1b2c3d4e5
Revises: e7883b1f7c8d
Create Date: 2026-09-28 12:46:50.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9a1b2c3d4e5'
down_revision = 'e7883b1f7c8d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('supplier_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('exchange_rate', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('total_with_exchange', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('bank_charges_currency', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('bank_charges', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('swift_charges', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('total_outflow', sa.Numeric(precision=18, scale=2), nullable=True))


def downgrade():
    with op.batch_alter_table('supplier_payments', schema=None) as batch_op:
        batch_op.drop_column('total_outflow')
        batch_op.drop_column('swift_charges')
        batch_op.drop_column('bank_charges')
        batch_op.drop_column('bank_charges_currency')
        batch_op.drop_column('total_with_exchange')
        batch_op.drop_column('exchange_rate')
