"""add extra fields to supplier_quotations and supplier_quotation_items

Revision ID: 456a26c9bba7
Revises: 3a4f4d00dfd1
Create Date: 2026-11-02 12:30:50.568770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '456a26c9bba7'
down_revision = '3a4f4d00dfd1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('supplier_quotation_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sr_no', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('total_amount', sa.Numeric(precision=18, scale=2), nullable=True))

    with op.batch_alter_table('supplier_quotations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('supplier_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('currency_symbol', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('currency', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('total_net_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('total_gross_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('total_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(length=50), nullable=False, server_default='completed'))


def downgrade():
    with op.batch_alter_table('supplier_quotations', schema=None) as batch_op:
        batch_op.drop_column('status')
        batch_op.drop_column('total_amount')
        batch_op.drop_column('total_gross_amount')
        batch_op.drop_column('total_net_amount')
        batch_op.drop_column('currency')
        batch_op.drop_column('currency_symbol')
        batch_op.drop_column('supplier_name')

    with op.batch_alter_table('supplier_quotation_items', schema=None) as batch_op:
        batch_op.drop_column('total_amount')
        batch_op.drop_column('description')
        batch_op.drop_column('sr_no')
