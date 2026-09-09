"""update warranty certificates schema

Revision ID: a1c49e72b38f
Revises: f2b9a78c310d
Create Date: 2026-09-09 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1c49e72b38f'
down_revision = 'f2b9a78c310d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('warranty_certificates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('po_no', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('invoice_no', sa.String(length=100), nullable=True))

    op.execute("UPDATE warranty_certificates SET po_no = po_number WHERE po_no IS NULL AND po_number IS NOT NULL")
    op.execute("UPDATE warranty_certificates SET invoice_no = invoice_number WHERE invoice_no IS NULL AND invoice_number IS NOT NULL")

    with op.batch_alter_table('warranty_certificates', schema=None) as batch_op:
        batch_op.drop_column('po_number')
        batch_op.drop_column('invoice_number')


def downgrade():
    with op.batch_alter_table('warranty_certificates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('invoice_number', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('po_number', sa.String(length=100), nullable=True))

    op.execute("UPDATE warranty_certificates SET po_number = po_no WHERE po_number IS NULL AND po_no IS NOT NULL")
    op.execute("UPDATE warranty_certificates SET invoice_number = invoice_no WHERE invoice_number IS NULL AND invoice_no IS NOT NULL")

    with op.batch_alter_table('warranty_certificates', schema=None) as batch_op:
        batch_op.drop_column('invoice_no')
        batch_op.drop_column('po_no')
