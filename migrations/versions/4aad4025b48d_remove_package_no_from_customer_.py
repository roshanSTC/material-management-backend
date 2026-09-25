"""remove package_no from customer_delivery_packing_list_items

Revision ID: 4aad4025b48d
Revises: 14b8a28430ea
Create Date: 2026-09-25 15:49:27.642397

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4aad4025b48d'
down_revision = '14b8a28430ea'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customer_delivery_packing_list_items', schema=None) as batch_op:
        batch_op.drop_column('package_no')


def downgrade():
    with op.batch_alter_table('customer_delivery_packing_list_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('package_no', sa.String(length=100), nullable=True))
