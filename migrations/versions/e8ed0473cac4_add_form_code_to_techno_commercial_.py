"""add form_code to techno_commercial_tenders

Revision ID: e8ed0473cac4
Revises: 456a26c9bba7
Create Date: 2026-11-03 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8ed0473cac4'
down_revision = '456a26c9bba7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('techno_commercial_tenders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('form_code', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('techno_commercial_tenders', schema=None) as batch_op:
        batch_op.drop_column('form_code')

