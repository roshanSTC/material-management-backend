"""merge corrigendum and icb heads

Revision ID: 9004f9be42d1
Revises: cc97f7fa72d8, f7a8b9c0d1e2
Create Date: 2026-11-04 14:55:51.630007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9004f9be42d1'
down_revision = ('cc97f7fa72d8', 'f7a8b9c0d1e2')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
