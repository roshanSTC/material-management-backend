"""dynamic 28 forms workflow

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-10-17 12:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a1'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


FORM_DEFINITIONS_DATA = [
    (1, 'FORM_01_PQB', 'National Pre-Qualification Bid (PQB)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-file-edit', 'Pre-qualification bid terms, submission schedule, supply locations, and requirements', True),
    (2, 'FORM_02_PQB_BID_DOCUMENT', 'Bid Document for PQB', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-book', 'Documentation for PQB submission, dates, and recorded corrigendum count', False),
    (3, 'FORM_03_CORRIGENDUM', 'Corrigendum', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-sync', 'Corrigendum amendment notices issued against EOI, PQB, or Tender notices', False),
    (4, 'FORM_04_LTE', 'Limited Tender Enquiry (LTE)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-briefcase', 'LTE invitation terms, tender fee, EMD amounts, deadlines, and item specifications', True),
    (5, 'FORM_05_NAC', 'Notification of Award of Contract (NAC)', 'Pre-Bidding & Tenders', 'phase-2', 'pi pi-verified', 'Formal contract award notice and itemized awarded material price breakdown', True),
    (6, 'FORM_06_CONSULTANCY_INVOICE', 'Consultancy Invoice', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-receipt', 'Advisory and specialist consultancy invoices associated with the project', False),
    (7, 'FORM_07_EOI', 'Expression of Interest (EOI)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-compass', 'Expression of interest publication details, submission mode, and items required', True),
    (8, 'FORM_08_CUSTOMER_QUERY', 'Query from Customer', 'Sourcing & Quotations', 'phase-1', 'pi pi-question-circle', 'Direct inquiry from customer detailing specific material requirements and quantities', True),
    (9, 'FORM_09_RFQ', 'Request for Quotation (RFQ)', 'Sourcing & Quotations', 'phase-1', 'pi pi-send', 'Dispatch RFQ to prospective vendors and suppliers with requirements', True),
    (10, 'FORM_10_COST_SHEET', 'Cost Sheet', 'Sourcing & Quotations', 'phase-1', 'pi pi-calculator', 'Complete commercial cost matrix including duties, forex buffers, logistics, and margins', False),
    (11, 'FORM_11_SUPPLIER_QUOTATION', 'Quotation from Supplier', 'Sourcing & Quotations', 'phase-1', 'pi pi-tags', 'Detailed quotation received from vendor with HSN/SAC codes, incoterms, and pricing', True),
    (12, 'FORM_12_CUSTOMER_QUOTATION', 'Quotation to Customer', 'Sourcing & Quotations', 'phase-1', 'pi pi-file-o', 'Final commercial offer sent to customer with itemized rates and validity', True),
    (13, 'FORM_13_PAC_TENDER', 'PAC Tender', 'Pre-Bidding & Tenders', 'phase-2', 'pi pi-building', 'Proprietary Article Certificate (PAC) tender enquiry terms, dates, and specifications', True),
    (14, 'FORM_14_PURCHASE_ORDER', 'Purchase Order (PO)', 'Supplier Orders & Invoices', 'phase-2', 'pi pi-shopping-bag', 'Formal purchase order contractual commitment with delivery dates and items', True),
    (15, 'FORM_15_BID_DOCUMENT', 'Bid Document', 'Pre-Bidding & Tenders', 'phase-2', 'pi pi-folder-open', 'Bid submission submission data, corrigendum counts, and quoted tender pricing', True),
    (16, 'FORM_16_ORDER_CONFIRMATION', 'Order Confirmation to Supplier', 'Supplier Orders & Invoices', 'phase-2', 'pi pi-check-square', 'Acknowledgement and formal confirmation placed with supplier for production', True),
    (17, 'FORM_17_PROFORMA_INVOICE', 'Supplier\'s Proforma Invoice', 'Supplier Orders & Invoices', 'phase-2', 'pi pi-file-invoice', 'Proforma invoice received from vendor prior to dispatch / foreign remittance', True),
    (18, 'FORM_18_SUPPLIER_INVOICE', 'Supplier\'s Invoice', 'Supplier Orders & Invoices', 'phase-3', 'pi pi-receipt', 'Commercial invoice issued by supplier covering final shipped goods', True),
    (19, 'FORM_19_SUPPLIER_PACKING_LIST', 'Supplier\'s Packing List', 'Logistics & Customs', 'phase-3', 'pi pi-box', 'Inventory package list with tare/gross weights provided by the supplier', True),
    (20, 'FORM_20_PAYMENT_TO_SUPPLIER', 'Payment to Supplier', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-wallet', 'Forex remittance transfer, SWIFT debit advice, exchange rates, and balances', False),
    (21, 'FORM_21_TRANSPORTATION_DETAILS', 'Transportation Details', 'Logistics & Customs', 'phase-3', 'pi pi-truck', 'Inland transport details, carrier consignments, LR/AWB receipts and charges', False),
    (22, 'FORM_22_PAYMENT_FROM_CUSTOMER', 'Payment from Customer', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-dollar', 'Receivables from customer, TDS/LD deductions, and balance settlement', False),
    (23, 'FORM_23_WARRANTY_CERTIFICATE', 'Warranty Certificate', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-shield', 'Manufacturer warranty coverage document referencing PO and invoices', False),
    (24, 'FORM_24_DELIVERY_CHALLAN', 'Delivery Challan to Customer', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-send', 'Dispatch challan with material items and consignee acknowledgement proof', True),
    (25, 'FORM_25_CUSTOMER_PACKING_LIST', 'Packing List to Customer', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-box', 'Final packing list delivered to the customer with tare and box specifications', True),
    (26, 'FORM_26_TAX_INVOICE_CUSTOMER', 'Tax Invoice to Customer', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-file', 'Final sales tax invoice billed to the customer for complete supply and service', True),
    (27, 'FORM_27_SHIPPING_CLEARANCE', 'Shipping & Clearance', 'Logistics & Customs', 'phase-3', 'pi pi-globe', 'Port logistics, customs Bill of Entry (BOE), duties, IGST, and clearance tracking', False),
    (28, 'FORM_28_FREIGHT_CHA', 'Freight Forwarder / CHA Details', 'Logistics & Customs', 'phase-3', 'pi pi-users', 'Customs House Agent (CHA) invoices, freight handling disbursements and fee records', True)
]


def upgrade():
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Create form_definitions table
    op.create_table(
        'form_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_code', sa.String(length=60), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=80), nullable=False),
        sa.Column('phase_id', sa.String(length=30), nullable=False),
        sa.Column('icon', sa.String(length=60), server_default='pi pi-file', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('has_table', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('form_code')
    )

    # 2. Seed form_definitions
    form_def_table = sa.table(
        'form_definitions',
        sa.column('id', sa.Integer),
        sa.column('form_code', sa.String),
        sa.column('name', sa.String),
        sa.column('category', sa.String),
        sa.column('phase_id', sa.String),
        sa.column('icon', sa.String),
        sa.column('description', sa.Text),
        sa.column('has_table', sa.Boolean),
        sa.column('is_active', sa.Boolean),
    )

    op.bulk_insert(
        form_def_table,
        [
            {
                'id': row[0],
                'form_code': row[1],
                'name': row[2],
                'category': row[3],
                'phase_id': row[4],
                'icon': row[5],
                'description': row[6],
                'has_table': row[7],
                'is_active': True,
            }
            for row in FORM_DEFINITIONS_DATA
        ]
    )

    if is_postgres:
        op.execute("SELECT setval('form_definitions_id_seq', (SELECT MAX(id) FROM form_definitions))")

    # 3. Update project_steps
    if is_postgres:
        # Drop old constraints
        op.execute("ALTER TABLE project_steps DROP CONSTRAINT IF EXISTS ck_project_step_number")
        op.execute("ALTER TABLE project_steps DROP CONSTRAINT IF EXISTS ck_project_step_status")
        # Add columns if not exist
        op.execute("ALTER TABLE project_steps ADD COLUMN IF NOT EXISTS form_code VARCHAR(60) REFERENCES form_definitions(form_code)")
        op.execute("ALTER TABLE project_steps ADD COLUMN IF NOT EXISTS step_order INT")
        op.execute("ALTER TABLE project_steps ADD COLUMN IF NOT EXISTS progress_percentage INT DEFAULT 0")
        op.execute("ALTER TABLE project_steps ADD CONSTRAINT ck_project_step_status CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped'))")

        # Map legacy steps
        op.execute("UPDATE project_steps SET step_order = step_number WHERE step_order IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_08_CUSTOMER_QUERY' WHERE step_number = 1 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_09_RFQ' WHERE step_number = 2 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_11_SUPPLIER_QUOTATION' WHERE step_number = 3 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_10_COST_SHEET' WHERE step_number = 4 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_12_CUSTOMER_QUOTATION' WHERE step_number = 5 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_13_PAC_TENDER' WHERE step_number = 6 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_15_BID_DOCUMENT' WHERE step_number = 7 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_14_PURCHASE_ORDER' WHERE step_number = 8 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_16_ORDER_CONFIRMATION' WHERE step_number = 9 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_18_SUPPLIER_INVOICE' WHERE step_number = 10 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_27_SHIPPING_CLEARANCE' WHERE step_number = 11 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_21_TRANSPORTATION_DETAILS' WHERE step_number = 12 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_24_DELIVERY_CHALLAN' WHERE step_number = 13 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_22_PAYMENT_FROM_CUSTOMER' WHERE step_number = 14 AND form_code IS NULL")
        op.execute("UPDATE project_steps SET form_code = 'FORM_20_PAYMENT_TO_SUPPLIER' WHERE step_number = 15 AND form_code IS NULL")
    else:
        with op.batch_alter_table('project_steps', schema=None) as batch_op:
            batch_op.add_column(sa.Column('form_code', sa.String(length=60), nullable=True))
            batch_op.add_column(sa.Column('step_order', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('progress_percentage', sa.Integer(), server_default='0', nullable=True))

    # 4. Create project_step_remarks
    op.create_table(
        'project_step_remarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_name', sa.String(length=100), nullable=True),
        sa.Column('remark', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['project_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_step_remarks_step_id', 'project_step_remarks', ['step_id'])

    # 5. Create project_step_attachments
    op.create_table(
        'project_step_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('step_id', sa.Integer(), nullable=False),
        sa.Column('upload_key', sa.String(length=80), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['project_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_project_step_attachments_step_id', 'project_step_attachments', ['step_id'])


def downgrade():
    op.drop_table('project_step_attachments')
    op.drop_table('project_step_remarks')
    with op.batch_alter_table('project_steps', schema=None) as batch_op:
        batch_op.drop_column('progress_percentage')
        batch_op.drop_column('step_order')
        batch_op.drop_column('form_code')
    op.drop_table('form_definitions')

