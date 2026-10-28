"""add status and items to pqb bid documents

Revision ID: a999d7255390
Revises: cec5e7af652f
Create Date: 2026-10-28 12:41:21.256539

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a999d7255390'
down_revision = 'cec5e7af652f'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Add status column to pqb_bid_documents
    if is_postgres:
        op.execute("ALTER TABLE pqb_bid_documents ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'completed';")
    else:
        with op.batch_alter_table('pqb_bid_documents') as batch_op:
            batch_op.add_column(sa.Column('status', sa.String(length=30), server_default='completed', nullable=True))

    # 2. Create pqb_bid_document_items table
    op.create_table(
        'pqb_bid_document_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pqb_bid_document_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=True),
        sa.Column('hsn_sac', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['pqb_bid_document_id'], ['pqb_bid_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pqb_bid_doc_items_doc_id', 'pqb_bid_document_items', ['pqb_bid_document_id'])

    # 3. Update has_table in form_definitions for FORM_02_PQB_BID_DOCUMENT
    op.execute(
        sa.text(
            "UPDATE form_definitions SET has_table = true WHERE form_code = 'FORM_02_PQB_BID_DOCUMENT';"
        )
    )


def downgrade():
    op.drop_table('pqb_bid_document_items')
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    if is_postgres:
        op.execute("ALTER TABLE pqb_bid_documents DROP COLUMN IF EXISTS status;")
    else:
        with op.batch_alter_table('pqb_bid_documents') as batch_op:
            batch_op.drop_column('status')
    op.execute(
        sa.text(
            "UPDATE form_definitions SET has_table = false WHERE form_code = 'FORM_02_PQB_BID_DOCUMENT';"
        )
    )
