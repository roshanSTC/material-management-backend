"""add entity_id to step_remarks

Revision ID: e2f891a27b14
Revises: 5af1fc57ffff
Create Date: 2026-09-24 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2f891a27b14'
down_revision = '5af1fc57ffff'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('step_remarks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('entity_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_step_remarks_entity_id'), ['entity_id'], unique=False)


def downgrade():
    with op.batch_alter_table('step_remarks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_step_remarks_entity_id'))
        batch_op.drop_column('entity_id')
