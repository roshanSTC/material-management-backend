"""allow null customer and supplier for disassociation

Revision ID: 8f1c3d5e7a9b
Revises: 70dfdde4a82b
Create Date: 2026-09-23 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f1c3d5e7a9b'
down_revision = '70dfdde4a82b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column('customer_id', existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('customer_queries', schema=None) as batch_op:
        batch_op.alter_column('customer_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('customer_quotations', schema=None) as batch_op:
        batch_op.alter_column('customer_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.alter_column('customer_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('quotation_requests', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('supplier_quotations', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('supplier_order_confirmations', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('supplier_proforma_invoices', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('supplier_invoices', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('supplier_packing_lists', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=True)


def downgrade():
    with op.batch_alter_table('supplier_packing_lists', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('supplier_invoices', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('supplier_proforma_invoices', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('supplier_order_confirmations', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('supplier_quotations', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('quotation_requests', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.alter_column('customer_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('customer_quotations', schema=None) as batch_op:
        batch_op.alter_column('customer_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('customer_queries', schema=None) as batch_op:
        batch_op.alter_column('customer_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column('supplier_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('customer_id', existing_type=sa.Integer(), nullable=False)

