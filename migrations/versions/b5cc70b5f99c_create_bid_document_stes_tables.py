"""create bid_document_stes tables

Revision ID: b5cc70b5f99c
Revises: e8ed0473cac4
Create Date: 2026-11-03 15:12:36.400082

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5cc70b5f99c'
down_revision = 'e8ed0473cac4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('bid_document_stes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('tender_title', sa.String(length=255), nullable=True),
        sa.Column('tender_no', sa.String(length=100), nullable=True),
        sa.Column('tender_issue_date', sa.Date(), nullable=True),
        sa.Column('total_no_corrigendum_issued', sa.Integer(), nullable=True, default=0),
        sa.Column('bid_submission_date', sa.Date(), nullable=True),
        sa.Column('delivery_terms', sa.String(length=100), nullable=True),
        sa.Column('delivery_period', sa.String(length=100), nullable=True),
        sa.Column('bid_validity', sa.String(length=100), nullable=True),
        sa.Column('payment_terms', sa.String(length=100), nullable=True),
        sa.Column('warranty_period', sa.String(length=100), nullable=True),
        sa.Column('gst_pct', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('total_net_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_gross_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('gst_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=True, default='completed'),
        sa.Column('form_code', sa.String(length=100), nullable=True, default='FORM_34_BID_DOC_STE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('bid_document_stes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bid_document_stes_project_id'), ['project_id'], unique=False)

    op.create_table('bid_document_ste_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bid_document_ste_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=True),
        sa.Column('hsn_sac', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['bid_document_ste_id'], ['bid_document_stes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('bid_document_ste_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bid_document_ste_items_bid_document_ste_id'), ['bid_document_ste_id'], unique=False)


def downgrade():
    op.drop_table('bid_document_ste_items')
    op.drop_table('bid_document_stes')
