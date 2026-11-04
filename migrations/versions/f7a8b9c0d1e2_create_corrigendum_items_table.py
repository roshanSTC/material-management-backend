"""create corrigendum_items table and enable table in form_definitions

Revision ID: f7a8b9c0d1e2
Revises: b5cc70b5f99c
Create Date: 2026-11-04 12:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7a8b9c0d1e2'
down_revision = 'b5cc70b5f99c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'corrigendum_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('corrigendum_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('as_per_tender_doc', sa.Text(), nullable=True),
        sa.Column('as_per_corrigendum', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['corrigendum_id'], ['corrigendums.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('corrigendum_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_corrigendum_items_corrigendum_id'), ['corrigendum_id'], unique=False)

    # Enable has_table for FORM_03_CORRIGENDUM in form_definitions catalog
    op.execute("UPDATE form_definitions SET has_table = TRUE WHERE form_code = 'FORM_03_CORRIGENDUM'")


def downgrade():
    op.execute("UPDATE form_definitions SET has_table = FALSE WHERE form_code = 'FORM_03_CORRIGENDUM'")
    with op.batch_alter_table('corrigendum_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_corrigendum_items_corrigendum_id'))
    op.drop_table('corrigendum_items')

