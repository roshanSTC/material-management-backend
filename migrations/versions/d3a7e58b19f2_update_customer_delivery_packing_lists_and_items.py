"""update customer delivery packing lists and items schema

Revision ID: d3a7e58b19f2
Revises: c7b2a9e140d3
Create Date: 2026-09-08 17:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3a7e58b19f2'
down_revision = 'c7b2a9e140d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customer_delivery_packing_lists', schema=None) as batch_op:
        batch_op.add_column(sa.Column('packing_list_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('net_weight', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('gross_weight', sa.String(length=255), nullable=True))

    op.execute("UPDATE customer_delivery_packing_lists SET packing_list_no = packing_list_number WHERE packing_list_no IS NULL")

    with op.batch_alter_table('customer_delivery_packing_lists', schema=None) as batch_op:
        batch_op.alter_column('packing_list_no', existing_type=sa.String(length=100), nullable=False)
        batch_op.drop_column('packing_list_number')
        batch_op.drop_column('net_weight_kg')
        batch_op.drop_column('gross_weight_kg')

    with op.batch_alter_table('customer_delivery_packing_list_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('package_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('material_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('hsn_code', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('weight', sa.Numeric(precision=18, scale=3), nullable=True))

    op.execute("UPDATE customer_delivery_packing_list_items SET material_name = material_description WHERE material_name IS NULL")
    op.execute("UPDATE customer_delivery_packing_list_items SET hsn_code = hsn_sac WHERE hsn_code IS NULL")
    op.execute("UPDATE customer_delivery_packing_list_items SET weight = total_weight_kg WHERE weight IS NULL")

    with op.batch_alter_table('customer_delivery_packing_list_items', schema=None) as batch_op:
        batch_op.alter_column('material_name', existing_type=sa.String(length=255), nullable=False)
        batch_op.drop_column('material_description')
        batch_op.drop_column('hsn_sac')
        batch_op.drop_column('weight_per_unit_kg')
        batch_op.drop_column('total_weight_kg')


def downgrade():
    with op.batch_alter_table('customer_delivery_packing_list_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('total_weight_kg', sa.Numeric(precision=18, scale=3), nullable=True))
        batch_op.add_column(sa.Column('weight_per_unit_kg', sa.Numeric(precision=18, scale=3), nullable=True))
        batch_op.add_column(sa.Column('hsn_sac', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('material_description', sa.String(length=500), nullable=True))

    op.execute("UPDATE customer_delivery_packing_list_items SET material_description = material_name WHERE material_description IS NULL")
    op.execute("UPDATE customer_delivery_packing_list_items SET hsn_sac = hsn_code WHERE hsn_sac IS NULL")
    op.execute("UPDATE customer_delivery_packing_list_items SET total_weight_kg = weight WHERE total_weight_kg IS NULL")

    with op.batch_alter_table('customer_delivery_packing_list_items', schema=None) as batch_op:
        batch_op.alter_column('material_description', existing_type=sa.String(length=500), nullable=False)
        batch_op.drop_column('weight')
        batch_op.drop_column('hsn_code')
        batch_op.drop_column('material_name')
        batch_op.drop_column('package_no')

    with op.batch_alter_table('customer_delivery_packing_lists', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gross_weight_kg', sa.Numeric(precision=18, scale=3), nullable=True))
        batch_op.add_column(sa.Column('net_weight_kg', sa.Numeric(precision=18, scale=3), nullable=True))
        batch_op.add_column(sa.Column('packing_list_number', sa.String(length=100), nullable=True))

    op.execute("UPDATE customer_delivery_packing_lists SET packing_list_number = packing_list_no WHERE packing_list_number IS NULL")

    with op.batch_alter_table('customer_delivery_packing_lists', schema=None) as batch_op:
        batch_op.alter_column('packing_list_number', existing_type=sa.String(length=100), nullable=False)
        batch_op.drop_column('gross_weight')
        batch_op.drop_column('net_weight')
        batch_op.drop_column('packing_list_no')

