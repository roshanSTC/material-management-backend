"""drop description from supplier_order_confirmation_items

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-11-26 15:47:10.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('supplier_order_confirmation_items', schema=None) as batch_op:
        batch_op.drop_column('description')


def downgrade():
    with op.batch_alter_table('supplier_order_confirmation_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.String(length=500), nullable=False, server_default=''))
