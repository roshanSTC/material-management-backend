"""create tables for forms 29 30 31

Revision ID: cec5e7af652f
Revises: 7e3e892f2b9c
Create Date: 2026-10-28 11:57:34.674801

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cec5e7af652f'
down_revision = '7e3e892f2b9c'
branch_labels = None
depends_on = None

NEW_FORM_DEFINITIONS = [
    (29, 'FORM_29_BID_DOC_TECHNO_COMMERCIAL', 'Bid Document (Techno-Commercial)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-file-edit', 'Techno-commercial bid document submission, terms, corrigendum count, and items', True),
    (30, 'FORM_30_TECHNO_COMMERCIAL_TENDER', 'Techno-Commercial Tender', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-briefcase', 'Techno-commercial tender enquiry terms, tender fee, EMD, schedule, and items', True),
    (31, 'FORM_31_BID_DOC_LTE', 'Bid Document for LTE', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-book', 'Limited Tender Enquiry (LTE) bid document submission, terms, corrigendum, and items', True),
]


def upgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. bid_document_techno_commercials
    op.create_table(
        'bid_document_techno_commercials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('tender_title', sa.String(length=255), nullable=True),
        sa.Column('tender_no', sa.String(length=100), nullable=True),
        sa.Column('tender_issue_date', sa.Date(), nullable=True),
        sa.Column('total_no_corrigendum_issued', sa.Integer(), server_default='0', nullable=True),
        sa.Column('bid_submission_date', sa.Date(), nullable=True),
        sa.Column('delivery_terms', sa.String(length=100), nullable=True),
        sa.Column('delivery_period', sa.String(length=100), nullable=True),
        sa.Column('bid_validity', sa.String(length=100), nullable=True),
        sa.Column('payment_terms', sa.String(length=100), nullable=True),
        sa.Column('warranty_period', sa.String(length=100), nullable=True),
        sa.Column('gst_pct', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='completed', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bid_doc_tc_project_id', 'bid_document_techno_commercials', ['project_id'])

    # 1b. bid_document_techno_commercial_items
    op.create_table(
        'bid_document_techno_commercial_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bid_document_techno_commercial_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=True),
        sa.Column('hsn_sac', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['bid_document_techno_commercial_id'], ['bid_document_techno_commercials.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bid_doc_tc_items_parent_id', 'bid_document_techno_commercial_items', ['bid_document_techno_commercial_id'])

    # 2. techno_commercial_tenders
    op.create_table(
        'techno_commercial_tenders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('pqb_no', sa.String(length=100), nullable=True),
        sa.Column('tender_title', sa.String(length=255), nullable=True),
        sa.Column('tender_no', sa.String(length=100), nullable=True),
        sa.Column('tender_issue_date', sa.Date(), nullable=True),
        sa.Column('bid_submission_due_date_time', sa.DateTime(), nullable=True),
        sa.Column('bid_opening_date_time', sa.DateTime(), nullable=True),
        sa.Column('tender_fee', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('emd', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('tender_validity', sa.String(length=100), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='completed', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tc_tender_project_id', 'techno_commercial_tenders', ['project_id'])

    # 2b. techno_commercial_tender_items
    op.create_table(
        'techno_commercial_tender_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('techno_commercial_tender_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['techno_commercial_tender_id'], ['techno_commercial_tenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tc_tender_items_parent_id', 'techno_commercial_tender_items', ['techno_commercial_tender_id'])

    # 3. bid_document_ltes
    op.create_table(
        'bid_document_ltes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('tender_title', sa.String(length=255), nullable=True),
        sa.Column('tender_no', sa.String(length=100), nullable=True),
        sa.Column('tender_issue_date', sa.Date(), nullable=True),
        sa.Column('total_no_corrigendum_issued', sa.Integer(), server_default='0', nullable=True),
        sa.Column('bid_submission_date', sa.Date(), nullable=True),
        sa.Column('delivery_terms', sa.String(length=100), nullable=True),
        sa.Column('delivery_period', sa.String(length=100), nullable=True),
        sa.Column('bid_validity', sa.String(length=100), nullable=True),
        sa.Column('payment_terms', sa.String(length=100), nullable=True),
        sa.Column('warranty_period', sa.String(length=100), nullable=True),
        sa.Column('gst_pct', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=30), server_default='completed', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bid_doc_lte_project_id', 'bid_document_ltes', ['project_id'])

    # 3b. bid_document_lte_items
    op.create_table(
        'bid_document_lte_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bid_document_lte_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=True),
        sa.Column('hsn_sac', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['bid_document_lte_id'], ['bid_document_ltes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bid_doc_lte_items_parent_id', 'bid_document_lte_items', ['bid_document_lte_id'])

    # 4. Insert seeds into form_definitions
    for row in NEW_FORM_DEFINITIONS:
        if is_postgres:
            op.execute(
                sa.text(
                    """
                    INSERT INTO form_definitions (id, form_code, name, category, phase_id, icon, description, has_table, is_active)
                    VALUES (:id, :form_code, :name, :category, :phase_id, :icon, :description, :has_table, :is_active)
                    ON CONFLICT (form_code) DO UPDATE SET
                        name = EXCLUDED.name,
                        category = EXCLUDED.category,
                        phase_id = EXCLUDED.phase_id,
                        icon = EXCLUDED.icon,
                        description = EXCLUDED.description,
                        has_table = EXCLUDED.has_table,
                        is_active = EXCLUDED.is_active;
                    """
                ).params(
                    id=row[0],
                    form_code=row[1],
                    name=row[2],
                    category=row[3],
                    phase_id=row[4],
                    icon=row[5],
                    description=row[6],
                    has_table=row[7],
                    is_active=True,
                )
            )
        else:
            op.execute(
                sa.text(
                    """
                    INSERT OR REPLACE INTO form_definitions (id, form_code, name, category, phase_id, icon, description, has_table, is_active)
                    VALUES (:id, :form_code, :name, :category, :phase_id, :icon, :description, :has_table, :is_active);
                    """
                ).params(
                    id=row[0],
                    form_code=row[1],
                    name=row[2],
                    category=row[3],
                    phase_id=row[4],
                    icon=row[5],
                    description=row[6],
                    has_table=row[7],
                    is_active=True,
                )
            )

    if is_postgres:
        op.execute("SELECT setval('form_definitions_id_seq', (SELECT MAX(id) FROM form_definitions))")


def downgrade():
    op.drop_table('bid_document_lte_items')
    op.drop_table('bid_document_ltes')
    op.drop_table('techno_commercial_tender_items')
    op.drop_table('techno_commercial_tenders')
    op.drop_table('bid_document_techno_commercial_items')
    op.drop_table('bid_document_techno_commercials')
    op.execute("DELETE FROM form_definitions WHERE form_code IN ('FORM_29_BID_DOC_TECHNO_COMMERCIAL', 'FORM_30_TECHNO_COMMERCIAL_TENDER', 'FORM_31_BID_DOC_LTE');")
