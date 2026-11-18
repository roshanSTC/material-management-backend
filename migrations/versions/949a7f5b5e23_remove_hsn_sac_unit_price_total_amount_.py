"""remove hsn_sac unit_price total_amount from pqb_bid_document_items

Revision ID: 949a7f5b5e23
Revises: 9004f9be42d1
Create Date: 2026-11-18 11:34:28.978316

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '949a7f5b5e23'
down_revision = '9004f9be42d1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("ALTER TABLE pqb_bid_document_items DROP COLUMN IF EXISTS hsn_sac;")
        op.execute("ALTER TABLE pqb_bid_document_items DROP COLUMN IF EXISTS unit_price;")
        op.execute("ALTER TABLE pqb_bid_document_items DROP COLUMN IF EXISTS total_amount;")
    else:
        with op.batch_alter_table('pqb_bid_document_items', schema=None) as batch_op:
            batch_op.drop_column('hsn_sac')
            batch_op.drop_column('unit_price')
            batch_op.drop_column('total_amount')


def downgrade():
    with op.batch_alter_table('pqb_bid_document_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hsn_sac', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=True))
        batch_op.add_column(sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True))
