from datetime import datetime

from app.extensions.database import db


class FormDefinition(db.Model):
    __tablename__ = "form_definitions"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    form_code = db.Column(
        db.String(60),
        unique=True,
        nullable=False,
        index=True,
    )
    name = db.Column(
        db.String(150),
        nullable=False,
    )
    category = db.Column(
        db.String(80),
        nullable=False,
    )
    phase_id = db.Column(
        db.String(30),
        nullable=False,
        index=True,
    )
    icon = db.Column(
        db.String(60),
        default="pi pi-file",
    )
    description = db.Column(
        db.Text,
        nullable=True,
    )
    has_table = db.Column(
        db.Boolean,
        default=False,
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "form_code": self.form_code,
            "name": self.name,
            "category": self.category,
            "phase_id": self.phase_id,
            "icon": self.icon,
            "description": self.description or "",
            "has_table": bool(self.has_table),
        }

    def __repr__(self) -> str:
        return f"<FormDefinition {self.form_code}: {self.name}>"


FORM_DEFINITIONS_SEED = [
    # 1..7: Pre-Bidding & Tenders (phase-1)
    (1, 'FORM_01_PQB', 'National Pre-Qualification Bid (PQB)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-file-edit', 'Pre-qualification bid terms, submission schedule, supply locations, and requirements', True),
    (2, 'FORM_02_PQB_BID_DOCUMENT', 'Bid Document for PQB', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-book', 'Documentation for PQB submission, dates, and recorded corrigendum count', False),
    (3, 'FORM_03_CORRIGENDUM', 'Corrigendum', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-sync', 'Corrigendum amendment notices issued against EOI, PQB, or Tender notices', False),
    (4, 'FORM_04_LTE', 'Limited Tender Enquiry (LTE)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-briefcase', 'LTE invitation terms, tender fee, EMD amounts, deadlines, and item specifications', True),
    (5, 'FORM_05_NAC', 'Notification of Award of Contract (NAC)', 'Pre-Bidding & Tenders', 'phase-2', 'pi pi-verified', 'Formal contract award notice and itemized awarded material price breakdown', True),
    (6, 'FORM_06_CONSULTANCY_INVOICE', 'Consultancy Invoice', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-receipt', 'Advisory and specialist consultancy invoices associated with the project', False),
    (7, 'FORM_07_EOI', 'Expression of Interest (EOI)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-compass', 'Expression of interest publication details, submission mode, and items required', True),

    # 8..12: Sourcing & Quotations (phase-1)
    (8, 'FORM_08_CUSTOMER_QUERY', 'Query from Customer', 'Sourcing & Quotations', 'phase-1', 'pi pi-question-circle', 'Direct inquiry from customer detailing specific material requirements and quantities', True),
    (9, 'FORM_09_RFQ', 'Request for Quotation (RFQ)', 'Sourcing & Quotations', 'phase-1', 'pi pi-send', 'Dispatch RFQ to prospective vendors and suppliers with requirements', True),
    (10, 'FORM_10_COST_SHEET', 'Cost Sheet', 'Sourcing & Quotations', 'phase-1', 'pi pi-calculator', 'Complete commercial cost matrix including duties, forex buffers, logistics, and margins', False),
    (11, 'FORM_11_SUPPLIER_QUOTATION', 'Quotation from Supplier', 'Sourcing & Quotations', 'phase-1', 'pi pi-tags', 'Detailed quotation received from vendor with HSN/SAC codes, incoterms, and pricing', True),
    (12, 'FORM_12_CUSTOMER_QUOTATION', 'Quotation to Customer', 'Sourcing & Quotations', 'phase-1', 'pi pi-file-o', 'Final commercial offer sent to customer with itemized rates and validity', True),

    # 13..17: Phase-2 (Tenders & Supplier Orders)
    (13, 'FORM_13_PAC_TENDER', 'PAC Tender', 'Pre-Bidding & Tenders', 'phase-2', 'pi pi-building', 'Proprietary Article Certificate (PAC) tender enquiry terms, dates, and specifications', True),
    (14, 'FORM_14_PURCHASE_ORDER', 'Purchase Order (PO)', 'Supplier Orders & Invoices', 'phase-2', 'pi pi-shopping-bag', 'Formal purchase order contractual commitment with delivery dates and items', True),
    (15, 'FORM_15_BID_DOCUMENT', 'Bid Document', 'Pre-Bidding & Tenders', 'phase-2', 'pi pi-folder-open', 'Bid submission submission data, corrigendum counts, and quoted tender pricing', True),
    (16, 'FORM_16_ORDER_CONFIRMATION', 'Order Confirmation to Supplier', 'Supplier Orders & Invoices', 'phase-2', 'pi pi-check-square', 'Acknowledgement and formal confirmation placed with supplier for production', True),
    (17, 'FORM_17_PROFORMA_INVOICE', 'Supplier\'s Proforma Invoice', 'Supplier Orders & Invoices', 'phase-2', 'pi pi-file-invoice', 'Proforma invoice received from vendor prior to dispatch / foreign remittance', True),

    # 18..21, 27..28: Phase-3 (Logistics, Customs & Shipped Goods)
    (18, 'FORM_18_SUPPLIER_INVOICE', 'Supplier\'s Invoice', 'Supplier Orders & Invoices', 'phase-3', 'pi pi-receipt', 'Commercial invoice issued by supplier covering final shipped goods', True),
    (19, 'FORM_19_SUPPLIER_PACKING_LIST', 'Supplier\'s Packing List', 'Logistics & Customs', 'phase-3', 'pi pi-box', 'Inventory package list with tare/gross weights provided by the supplier', True),
    (21, 'FORM_21_TRANSPORTATION_DETAILS', 'Transportation Details', 'Logistics & Customs', 'phase-3', 'pi pi-truck', 'Inland transport details, carrier consignments, LR/AWB receipts and charges', False),
    (27, 'FORM_27_SHIPPING_CLEARANCE', 'Shipping & Clearance', 'Logistics & Customs', 'phase-3', 'pi pi-globe', 'Port logistics, customs Bill of Entry (BOE), duties, IGST, and clearance tracking', False),
    (28, 'FORM_28_FREIGHT_CHA', 'Freight Forwarder / CHA Details', 'Logistics & Customs', 'phase-3', 'pi pi-users', 'Customs House Agent (CHA) invoices, freight handling disbursements and fee records', True),

    # 20, 22..26: Phase-4 (Customer & Supplier Settlement)
    (20, 'FORM_20_PAYMENT_TO_SUPPLIER', 'Payment to Supplier', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-wallet', 'Forex remittance transfer, SWIFT debit advice, exchange rates, and balances', False),
    (22, 'FORM_22_PAYMENT_FROM_CUSTOMER', 'Payment from Customer', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-dollar', 'Receivables from customer, TDS/LD deductions, and balance settlement', False),
    (23, 'FORM_23_WARRANTY_CERTIFICATE', 'Warranty Certificate', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-shield', 'Manufacturer warranty coverage document referencing PO and invoices', False),
    (24, 'FORM_24_DELIVERY_CHALLAN', 'Delivery Challan to Customer', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-send', 'Dispatch challan with material items and consignee acknowledgement proof', True),
    (25, 'FORM_25_CUSTOMER_PACKING_LIST', 'Packing List to Customer', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-box', 'Final packing list delivered to the customer with tare and box specifications', True),
    (26, 'FORM_26_TAX_INVOICE_CUSTOMER', 'Tax Invoice to Customer', 'Customer & Supplier Settlement', 'phase-4', 'pi pi-file', 'Final sales tax invoice billed to the customer for complete supply and service', True),

    # 29..31: Additional Pre-Bidding & Tender Forms
    (29, 'FORM_29_BID_DOC_TECHNO_COMMERCIAL', 'Bid Document (Techno-Commercial)', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-file-edit', 'Techno-commercial bid document submission, terms, corrigendum count, and items', True),
    (30, 'FORM_30_TECHNO_COMMERCIAL_TENDER', 'Techno-Commercial Tender', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-briefcase', 'Techno-commercial tender enquiry terms, tender fee, EMD, schedule, and items', True),
    (31, 'FORM_31_BID_DOC_LTE', 'Bid Document for LTE', 'Pre-Bidding & Tenders', 'phase-1', 'pi pi-book', 'Limited Tender Enquiry (LTE) bid document submission, terms, corrigendum, and items', True),
]


def seed_form_definitions():
    for row in FORM_DEFINITIONS_SEED:
        existing = FormDefinition.query.filter_by(form_code=row[1]).first()
        if existing:
            existing.name = row[2]
            existing.category = row[3]
            existing.phase_id = row[4]
            existing.icon = row[5]
            existing.description = row[6]
            existing.has_table = row[7]
            existing.is_active = True
        else:
            f = FormDefinition(
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
            db.session.add(f)
    db.session.commit()
