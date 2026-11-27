"""add currency fields to bid_submissions, notification_awards, and purchase_orders

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-11-27 12:54:10.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bid_submissions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency_unit', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('currency_symbol', sa.String(length=20), nullable=True))

    with op.batch_alter_table('bid_submission_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(length=20), nullable=True))

    with op.batch_alter_table('notification_awards', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency_unit', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('currency_symbol', sa.String(length=20), nullable=True))

    with op.batch_alter_table('notification_award_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(length=20), nullable=True))

    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency_unit', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('currency_symbol', sa.String(length=20), nullable=True))

    with op.batch_alter_table('purchase_order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('purchase_order_items', schema=None) as batch_op:
        batch_op.drop_column('currency')

    with op.batch_alter_table('purchase_orders', schema=None) as batch_op:
        batch_op.drop_column('currency_symbol')
        batch_op.drop_column('currency_unit')

    with op.batch_alter_table('notification_award_items', schema=None) as batch_op:
        batch_op.drop_column('currency')

    with op.batch_alter_table('notification_awards', schema=None) as batch_op:
        batch_op.drop_column('currency_symbol')
        batch_op.drop_column('currency_unit')

    with op.batch_alter_table('bid_submission_items', schema=None) as batch_op:
        batch_op.drop_column('currency')

    with op.batch_alter_table('bid_submissions', schema=None) as batch_op:
        batch_op.drop_column('currency_symbol')
        batch_op.drop_column('currency_unit')
