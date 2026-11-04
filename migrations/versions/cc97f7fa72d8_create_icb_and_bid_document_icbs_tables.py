"""create icb and bid_document_icbs tables

Revision ID: cc97f7fa72d8
Revises: b5cc70b5f99c
Create Date: 2026-11-04 10:58:23.858494

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc97f7fa72d8'
down_revision = 'b5cc70b5f99c'
branch_labels = None
depends_on = None


def upgrade():
    # 1. international_competitive_biddings
    op.create_table(
        'international_competitive_biddings',
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
        sa.Column('status', sa.String(length=30), nullable=True, server_default='completed'),
        sa.Column('form_code', sa.String(length=100), nullable=True, server_default='FORM_35_ICB'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('international_competitive_biddings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_international_competitive_biddings_project_id'), ['project_id'], unique=False)

    # 2. international_competitive_bidding_items
    op.create_table(
        'international_competitive_bidding_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('international_competitive_bidding_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['international_competitive_bidding_id'], ['international_competitive_biddings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('international_competitive_bidding_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_international_competitive_bidding_items_international_competitive_bidding_id'), ['international_competitive_bidding_id'], unique=False)

    # 3. bid_document_icbs
    op.create_table(
        'bid_document_icbs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('tender_title', sa.String(length=255), nullable=True),
        sa.Column('tender_no', sa.String(length=100), nullable=True),
        sa.Column('tender_issue_date', sa.Date(), nullable=True),
        sa.Column('total_no_corrigendum_issued', sa.Integer(), nullable=True, server_default='0'),
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
        sa.Column('status', sa.String(length=30), nullable=True, server_default='completed'),
        sa.Column('form_code', sa.String(length=100), nullable=True, server_default='FORM_36_BID_DOC_ICB'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('bid_document_icbs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bid_document_icbs_project_id'), ['project_id'], unique=False)

    # 4. bid_document_icb_items
    op.create_table(
        'bid_document_icb_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bid_document_icb_id', sa.Integer(), nullable=False),
        sa.Column('sr_no', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('material_name', sa.String(length=255), nullable=True),
        sa.Column('item_code', sa.String(length=100), nullable=True),
        sa.Column('hsn_sac', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=15, scale=3), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['bid_document_icb_id'], ['bid_document_icbs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('bid_document_icb_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_bid_document_icb_items_bid_document_icb_id'), ['bid_document_icb_id'], unique=False)

    # 5. Seed form_definitions
    op.execute("""
        INSERT INTO form_definitions (id, form_code, name, category, phase_id, icon, description, has_table, is_active, created_at)
        VALUES 
          (35, 'FORM_35_ICB', 'International Competitive Bidding (ICB)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-globe', 'International Competitive Bidding (ICB) terms, tender fee, EMD, schedule, and items', true, true, NOW()),
          (36, 'FORM_36_BID_DOC_ICB', 'Bid Document for ICB', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-book', 'Bid Document for International Competitive Bidding (ICB), terms, corrigendum, items, and values', true, true, NOW())
        ON CONFLICT (id) DO UPDATE SET 
          form_code = EXCLUDED.form_code,
          name = EXCLUDED.name,
          category = EXCLUDED.category,
          phase_id = EXCLUDED.phase_id,
          icon = EXCLUDED.icon,
          description = EXCLUDED.description,
          has_table = EXCLUDED.has_table,
          is_active = EXCLUDED.is_active;
    """)


def downgrade():
    op.execute("""
        DELETE FROM form_definitions WHERE id IN (35, 36) OR form_code IN ('FORM_35_ICB', 'FORM_36_BID_DOC_ICB');
    """)
    op.drop_table('bid_document_icb_items')
    op.drop_table('bid_document_icbs')
    op.drop_table('international_competitive_bidding_items')
    op.drop_table('international_competitive_biddings')
