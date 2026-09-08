"""update customer delivery invoices and items schema

Revision ID: c7b2a9e140d3
Revises: e991b42fdaca
Create Date: 2026-09-08 17:08:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7b2a9e140d3'
down_revision = 'e991b42fdaca'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customer_delivery_invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invoice_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('gst_amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('net_total', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.alter_column('gst_rate', existing_type=sa.Numeric(precision=5, scale=2), type_=sa.Numeric(precision=18, scale=2), existing_nullable=True)

    op.execute("UPDATE customer_delivery_invoices SET invoice_no = invoice_number WHERE invoice_no IS NULL")

    with op.batch_alter_table('customer_delivery_invoices', schema=None) as batch_op:
        batch_op.alter_column('invoice_no', existing_type=sa.String(length=100), nullable=False)
        batch_op.drop_column('invoice_number')

    with op.batch_alter_table('customer_delivery_invoice_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('material_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('hsn_code', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('unit_price', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('net_amount', sa.Numeric(precision=18, scale=2), nullable=True))

    op.execute("UPDATE customer_delivery_invoice_items SET material_name = material_description WHERE material_name IS NULL")
    op.execute("UPDATE customer_delivery_invoice_items SET hsn_code = hsn_sac WHERE hsn_code IS NULL")
    op.execute("UPDATE customer_delivery_invoice_items SET unit_price = rate_per_unit WHERE unit_price IS NULL")
    op.execute("UPDATE customer_delivery_invoice_items SET net_amount = amount WHERE net_amount IS NULL")

    with op.batch_alter_table('customer_delivery_invoice_items', schema=None) as batch_op:
        batch_op.alter_column('material_name', existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column('unit_price', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.alter_column('net_amount', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.drop_column('material_description')
        batch_op.drop_column('hsn_sac')
        batch_op.drop_column('rate_per_unit')
        batch_op.drop_column('amount')


def downgrade():
    with op.batch_alter_table('customer_delivery_invoice_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('rate_per_unit', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('hsn_sac', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('material_description', sa.String(length=500), nullable=True))

    op.execute("UPDATE customer_delivery_invoice_items SET material_description = material_name WHERE material_description IS NULL")
    op.execute("UPDATE customer_delivery_invoice_items SET hsn_sac = hsn_code WHERE hsn_sac IS NULL")
    op.execute("UPDATE customer_delivery_invoice_items SET rate_per_unit = unit_price WHERE rate_per_unit IS NULL")
    op.execute("UPDATE customer_delivery_invoice_items SET amount = net_amount WHERE amount IS NULL")

    with op.batch_alter_table('customer_delivery_invoice_items', schema=None) as batch_op:
        batch_op.alter_column('material_description', existing_type=sa.String(length=500), nullable=False)
        batch_op.alter_column('rate_per_unit', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.alter_column('amount', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.drop_column('net_amount')
        batch_op.drop_column('unit_price')
        batch_op.drop_column('hsn_code')
        batch_op.drop_column('material_name')

    with op.batch_alter_table('customer_delivery_invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invoice_number', sa.String(length=100), nullable=True))

    op.execute("UPDATE customer_delivery_invoices SET invoice_number = invoice_no WHERE invoice_number IS NULL")

    with op.batch_alter_table('customer_delivery_invoices', schema=None) as batch_op:
        batch_op.alter_column('invoice_number', existing_type=sa.String(length=100), nullable=False)
        batch_op.alter_column('gst_rate', existing_type=sa.Numeric(precision=18, scale=2), type_=sa.Numeric(precision=5, scale=2), existing_nullable=True)
        batch_op.drop_column('net_total')
        batch_op.drop_column('gst_amount')
        batch_op.drop_column('invoice_no')

