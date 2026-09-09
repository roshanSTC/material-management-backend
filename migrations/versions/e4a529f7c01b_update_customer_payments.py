"""update customer payments schema

Revision ID: e4a529f7c01b
Revises: b2e519c83fa4
Create Date: 2026-09-09 12:49:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4a529f7c01b'
down_revision = 'b2e519c83fa4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customer_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invoice_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('ld', sa.Numeric(precision=18, scale=2), nullable=True))

    op.execute("UPDATE customer_payments SET invoice_no = invoice_number WHERE invoice_no IS NULL AND invoice_number IS NOT NULL")
    op.execute("UPDATE customer_payments SET ld = liquidated_damages WHERE ld IS NULL AND liquidated_damages IS NOT NULL")

    with op.batch_alter_table('customer_payments', schema=None) as batch_op:
        batch_op.alter_column('invoice_no', existing_type=sa.String(length=100), nullable=False)
        batch_op.drop_column('invoice_number')
        batch_op.drop_column('liquidated_damages')


def downgrade():
    with op.batch_alter_table('customer_payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('liquidated_damages', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('invoice_number', sa.String(length=100), nullable=True))

    op.execute("UPDATE customer_payments SET invoice_number = invoice_no WHERE invoice_number IS NULL AND invoice_no IS NOT NULL")
    op.execute("UPDATE customer_payments SET liquidated_damages = ld WHERE liquidated_damages IS NULL AND ld IS NOT NULL")

    with op.batch_alter_table('customer_payments', schema=None) as batch_op:
        batch_op.alter_column('invoice_number', existing_type=sa.String(length=100), nullable=False)
        batch_op.drop_column('ld')
        batch_op.drop_column('invoice_no')

