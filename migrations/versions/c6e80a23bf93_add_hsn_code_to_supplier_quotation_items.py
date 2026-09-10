"""add hsn_code to supplier_quotation_items

Revision ID: c6e80a23bf93
Revises: f5c639a8d12e
Create Date: 2026-09-10 12:47:21.624133

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c6e80a23bf93'
down_revision = 'f5c639a8d12e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('supplier_quotation_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hsn_code', sa.String(length=50), nullable=True))


def downgrade():
    with op.batch_alter_table('supplier_quotation_items', schema=None) as batch_op:
        batch_op.drop_column('hsn_code')

