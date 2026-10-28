"""add delivery_date and unit to purchase_order_items

Revision ID: 6d4bfaaec9ad
Revises: 90e2a66c4a3f
Create Date: 2026-10-28 17:01:36.837858

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d4bfaaec9ad'
down_revision = '90e2a66c4a3f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('purchase_order_items', sa.Column('delivery_date', sa.Date(), nullable=True))
    op.add_column('purchase_order_items', sa.Column('unit', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('purchase_order_items', 'unit')
    op.drop_column('purchase_order_items', 'delivery_date')
