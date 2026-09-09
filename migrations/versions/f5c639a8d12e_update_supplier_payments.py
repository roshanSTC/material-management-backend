"""update supplier payments schema

Revision ID: f5c639a8d12e
Revises: e4a529f7c01b
Create Date: 2026-09-09 14:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5c639a8d12e'
down_revision = 'e4a529f7c01b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('supplier_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('payment_percentage', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('total_supplier_value', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('amount_paid', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)

    op.execute("UPDATE supplier_payments SET amount_paid = COALESCE(amount_paid_inr, amount_paid_currency, 0)")

    with op.batch_alter_table('supplier_payments', schema=None) as batch_op:
        batch_op.alter_column('amount_paid', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.drop_column('amount_paid_currency')
        batch_op.drop_column('amount_paid_inr')


def downgrade():
    with op.batch_alter_table('supplier_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amount_paid_inr', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('amount_paid_currency', sa.Numeric(precision=18, scale=2), nullable=True))

    op.execute("UPDATE supplier_payments SET amount_paid_inr = amount_paid, amount_paid_currency = amount_paid")

    with op.batch_alter_table('supplier_payments', schema=None) as batch_op:
        batch_op.alter_column('amount_paid_inr', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.alter_column('amount_paid_currency', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('amount_paid')
        batch_op.drop_column('total_supplier_value')
        batch_op.drop_column('payment_percentage')
