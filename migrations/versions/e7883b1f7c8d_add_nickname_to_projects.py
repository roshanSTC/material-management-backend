"""add nickname to projects

Revision ID: e7883b1f7c8d
Revises: 723634c6d6b0
Create Date: 2026-09-28 11:24:48.047493

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7883b1f7c8d'
down_revision = '723634c6d6b0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nickname', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('nickname')

