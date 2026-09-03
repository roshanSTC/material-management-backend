"""drop unique constraint uq_quotation_request_project_supplier

Revision ID: f132403f7f44
Revises: d87e1294ab23
Create Date: 2026-09-03 15:12:58.382460

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f132403f7f44'
down_revision = 'd87e1294ab23'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('quotation_requests', schema=None) as batch_op:
        batch_op.drop_constraint('uq_quotation_request_project_supplier', type_='unique')


def downgrade():
    with op.batch_alter_table('quotation_requests', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_quotation_request_project_supplier', ['project_id', 'supplier_id'])

