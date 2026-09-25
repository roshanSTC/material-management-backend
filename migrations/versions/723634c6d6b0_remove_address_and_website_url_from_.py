"""remove address and website_url from customer and supplier

Revision ID: 723634c6d6b0
Revises: 4aad4025b48d
Create Date: 2026-09-25 16:51:43.660225

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '723634c6d6b0'
down_revision = '4aad4025b48d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_column('address')
        batch_op.drop_column('website_url')

    with op.batch_alter_table('suppliers', schema=None) as batch_op:
        batch_op.drop_column('address')
        batch_op.drop_column('website_url')


def downgrade():
    with op.batch_alter_table('suppliers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('website_url', sa.String(length=2048), nullable=True))
        batch_op.add_column(sa.Column('address', sa.Text(), nullable=True))

    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('website_url', sa.String(length=2048), nullable=True))
        batch_op.add_column(sa.Column('address', sa.Text(), nullable=True))
