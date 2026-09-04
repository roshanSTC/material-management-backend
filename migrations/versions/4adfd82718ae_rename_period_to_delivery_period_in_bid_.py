"""rename period to delivery_period in bid_submissions and drop total from bid_submission_items

Revision ID: 4adfd82718ae
Revises: 361f23c961e8
Create Date: 2026-09-04 17:53:19.604184

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4adfd82718ae'
down_revision = '361f23c961e8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bid_submission_items', schema=None) as batch_op:
        batch_op.drop_column('total')

    with op.batch_alter_table('bid_submissions', schema=None) as batch_op:
        batch_op.alter_column('period', new_column_name='delivery_period')


def downgrade():
    with op.batch_alter_table('bid_submissions', schema=None) as batch_op:
        batch_op.alter_column('delivery_period', new_column_name='period')

    with op.batch_alter_table('bid_submission_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('total', sa.NUMERIC(precision=18, scale=2), autoincrement=False, nullable=True))
