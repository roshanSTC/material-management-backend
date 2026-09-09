"""update delivery challans and items schema

Revision ID: f2b9a78c310d
Revises: d3a7e58b19f2
Create Date: 2026-09-08 18:16:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f2b9a78c310d'
down_revision = 'd3a7e58b19f2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('delivery_challans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delivery_challan_no', sa.String(length=100), nullable=True))

    op.execute("UPDATE delivery_challans SET delivery_challan_no = delivery_challan_number WHERE delivery_challan_no IS NULL")

    with op.batch_alter_table('delivery_challans', schema=None) as batch_op:
        batch_op.alter_column('delivery_challan_no', existing_type=sa.String(length=100), nullable=False)
        batch_op.drop_column('delivery_challan_number')

    with op.batch_alter_table('delivery_challan_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('material_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('hsn_code', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('unit_price', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('net_amount', sa.Numeric(precision=18, scale=2), nullable=True))

    op.execute("UPDATE delivery_challan_items SET material_name = material_description WHERE material_name IS NULL")
    op.execute("UPDATE delivery_challan_items SET unit_price = rate_per_unit WHERE unit_price IS NULL")
    op.execute("UPDATE delivery_challan_items SET net_amount = amount WHERE net_amount IS NULL")

    with op.batch_alter_table('delivery_challan_items', schema=None) as batch_op:
        batch_op.alter_column('material_name', existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column('unit_price', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.alter_column('net_amount', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.drop_column('material_description')
        batch_op.drop_column('rate_per_unit')
        batch_op.drop_column('amount')


def downgrade():
    with op.batch_alter_table('delivery_challan_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('amount', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('rate_per_unit', sa.Numeric(precision=18, scale=2), nullable=True))
        batch_op.add_column(sa.Column('material_description', sa.String(length=500), nullable=True))

    op.execute("UPDATE delivery_challan_items SET material_description = material_name WHERE material_description IS NULL")
    op.execute("UPDATE delivery_challan_items SET rate_per_unit = unit_price WHERE rate_per_unit IS NULL")
    op.execute("UPDATE delivery_challan_items SET amount = net_amount WHERE amount IS NULL")

    with op.batch_alter_table('delivery_challan_items', schema=None) as batch_op:
        batch_op.alter_column('material_description', existing_type=sa.String(length=500), nullable=False)
        batch_op.alter_column('rate_per_unit', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.alter_column('amount', existing_type=sa.Numeric(precision=18, scale=2), nullable=False)
        batch_op.drop_column('net_amount')
        batch_op.drop_column('unit_price')
        batch_op.drop_column('hsn_code')
        batch_op.drop_column('material_name')

    with op.batch_alter_table('delivery_challans', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delivery_challan_number', sa.String(length=100), nullable=True))

    op.execute("UPDATE delivery_challans SET delivery_challan_number = delivery_challan_no WHERE delivery_challan_number IS NULL")

    with op.batch_alter_table('delivery_challans', schema=None) as batch_op:
        batch_op.alter_column('delivery_challan_number', existing_type=sa.String(length=100), nullable=False)
        batch_op.drop_column('delivery_challan_no')

