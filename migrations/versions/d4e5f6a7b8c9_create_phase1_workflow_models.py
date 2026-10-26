"""create phase 1 workflow models

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-26 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # 1. pre_qualification_bids
    op.create_table(
        'pre_qualification_bids',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('pqb_title', sa.String(length=255), nullable=True),
        sa.Column('pqb_no', sa.String(length=100), nullable=False),
        sa.Column('pqb_issuing_date', sa.Date(), nullable=True),
        sa.Column('pqb_closing_date_time', sa.DateTime(), nullable=True),
        sa.Column('pqb_opening_date_time', sa.DateTime(), nullable=True),
        sa.Column('mode_of_bid_submission', sa.String(length=100), nullable=True),
        sa.Column('supply_location', sa.String(length=255), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pqb_project_id', 'pre_qualification_bids', ['project_id'])

    # 1b. pre_qualification_bid_items
    op.create_table(
        'pre_qualification_bid_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pre_qualification_bid_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['pre_qualification_bid_id'], ['pre_qualification_bids.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pqb_items_pqb_id', 'pre_qualification_bid_items', ['pre_qualification_bid_id'])

    # 2. pqb_bid_documents
    op.create_table(
        'pqb_bid_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('pqb_title', sa.String(length=255), nullable=True),
        sa.Column('pqb_no', sa.String(length=100), nullable=False),
        sa.Column('pqb_issue_date', sa.Date(), nullable=True),
        sa.Column('pqb_closing_date_time', sa.DateTime(), nullable=True),
        sa.Column('pqb_opening_date_time', sa.DateTime(), nullable=True),
        sa.Column('total_corrigendum_issued', sa.Integer(), server_default='0', nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pqb_docs_project_id', 'pqb_bid_documents', ['project_id'])

    # 3. corrigendums
    op.create_table(
        'corrigendums',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('corrigendum_no', sa.String(length=100), nullable=False),
        sa.Column('against_tender_no', sa.String(length=100), nullable=True),
        sa.Column('tender_title', sa.String(length=255), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_corrigendums_project_id', 'corrigendums', ['project_id'])

    # 4. limited_tender_enquiries
    op.create_table(
        'limited_tender_enquiries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('pqb_no', sa.String(length=100), nullable=True),
        sa.Column('tender_title', sa.String(length=255), nullable=True),
        sa.Column('tender_enquiry_no', sa.String(length=100), nullable=False),
        sa.Column('tender_issue_date', sa.Date(), nullable=True),
        sa.Column('bid_submission_due_date_time', sa.DateTime(), nullable=True),
        sa.Column('bid_opening_date_time', sa.DateTime(), nullable=True),
        sa.Column('tender_fee', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('emd', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('tender_validity', sa.String(length=100), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_lte_project_id', 'limited_tender_enquiries', ['project_id'])

    # 4b. limited_tender_enquiry_items
    op.create_table(
        'limited_tender_enquiry_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('limited_tender_enquiry_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['limited_tender_enquiry_id'], ['limited_tender_enquiries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_lte_items_lte_id', 'limited_tender_enquiry_items', ['limited_tender_enquiry_id'])

    # 5. notification_awards
    op.create_table(
        'notification_awards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('nac_no', sa.String(length=100), nullable=False),
        sa.Column('nac_date', sa.Date(), nullable=True),
        sa.Column('nac_title', sa.String(length=255), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_nac_project_id', 'notification_awards', ['project_id'])

    # 5b. notification_award_items
    op.create_table(
        'notification_award_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_award_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('per_unit_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['notification_award_id'], ['notification_awards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_nac_items_nac_id', 'notification_award_items', ['notification_award_id'])

    # 6. consultancy_invoices
    op.create_table(
        'consultancy_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('invoice_no', sa.String(length=100), nullable=False),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('party_name', sa.String(length=255), nullable=True),
        sa.Column('invoice_reference', sa.String(length=255), nullable=True),
        sa.Column('total_value_eur', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_consultancy_invoices_project_id', 'consultancy_invoices', ['project_id'])

    # 7. expressions_of_interest
    op.create_table(
        'expressions_of_interest',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('eoi_title', sa.String(length=255), nullable=True),
        sa.Column('eoi_no', sa.String(length=100), nullable=False),
        sa.Column('eoi_date', sa.Date(), nullable=True),
        sa.Column('eoi_closing_date_time', sa.DateTime(), nullable=True),
        sa.Column('eoi_opening_date_time', sa.DateTime(), nullable=True),
        sa.Column('mode_of_submission', sa.String(length=100), nullable=True),
        sa.Column('supply_location', sa.String(length=255), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_eoi_project_id', 'expressions_of_interest', ['project_id'])

    # 7b. expression_of_interest_items
    op.create_table(
        'expression_of_interest_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('expression_of_interest_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['expression_of_interest_id'], ['expressions_of_interest.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_eoi_items_eoi_id', 'expression_of_interest_items', ['expression_of_interest_id'])


def downgrade():
    op.drop_table('expression_of_interest_items')
    op.drop_table('expressions_of_interest')
    op.drop_table('consultancy_invoices')
    op.drop_table('notification_award_items')
    op.drop_table('notification_awards')
    op.drop_table('limited_tender_enquiry_items')
    op.drop_table('limited_tender_enquiries')
    op.drop_table('corrigendums')
    op.drop_table('pqb_bid_documents')
    op.drop_table('pre_qualification_bid_items')
    op.drop_table('pre_qualification_bids')

