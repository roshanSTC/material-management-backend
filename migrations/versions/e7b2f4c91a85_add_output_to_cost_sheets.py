"""add output to cost sheets and quotation fields to cost sheet items

Revision ID: e7b2f4c91a85
Revises: 137fa5374239
Create Date: 2026-09-02 18:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7b2f4c91a85'
down_revision = '137fa5374239'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('cost_sheets', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('output', sa.JSON(), nullable=False, server_default='{}')
        )

    with op.batch_alter_table('cost_sheet_items', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('quotation_number', sa.String(length=100), nullable=True)
        )
        batch_op.add_column(
            sa.Column('quotation_index', sa.String(length=100), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('cost_sheet_items', schema=None) as batch_op:
        batch_op.drop_column('quotation_index')
        batch_op.drop_column('quotation_number')

    with op.batch_alter_table('cost_sheets', schema=None) as batch_op:
        batch_op.drop_column('output')
