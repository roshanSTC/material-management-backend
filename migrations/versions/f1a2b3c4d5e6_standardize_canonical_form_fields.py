"""standardize canonical form codes and fields

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-11-25 17:22:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None


FORM_CODE_REWRITES = [
    ("FORM_13_CUSTOMER_TENDER", "FORM_13_PAC_TENDER"),
    ("FORM_29_BID_DOCUMENT_TECHNO_COMMERCIAL", "FORM_29_BID_DOC_TECHNO_COMMERCIAL"),
    ("FORM_30_TCT", "FORM_30_TECHNO_COMMERCIAL_TENDER"),
    ("FORM_30", "FORM_30_TECHNO_COMMERCIAL_TENDER"),
    ("FORM_31_BID_DOCUMENT_LTE", "FORM_31_BID_DOC_LTE"),
    ("FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33_STE"),
    ("FORM_33", "FORM_33_STE"),
    ("FORM_STE", "FORM_33_STE"),
    ("FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_33_STE"),
    ("FORM_30_STE", "FORM_33_STE"),
    ("FORM_34_BID_DOCUMENT_STE", "FORM_34_BID_DOC_STE"),
    ("FORM_35_INTERNATIONAL_COMPETITIVE_BIDDING", "FORM_35_ICB"),
    ("FORM_36_BID_DOCUMENT_ICB", "FORM_36_BID_DOC_ICB"),
]


def _drop_if_exists(table_name: str, column_name: str) -> None:
    op.execute(f'ALTER TABLE "{table_name}" DROP COLUMN IF EXISTS "{column_name}"')


def upgrade():
    # 1. Normalize any legacy form_code rows across form_definitions and workflow tables
    for table_name in (
        "form_definitions",
        "project_steps",
        "techno_commercial_tenders",
        "bid_document_stes",
        "bid_document_icbs",
        "international_competitive_biddings",
    ):
        for old_code, canonical_code in FORM_CODE_REWRITES:
            if table_name == "form_definitions":
                # Avoid unique violation if canonical row already exists
                op.execute(
                    f"""
                    DELETE FROM "{table_name}"
                    WHERE form_code = '{old_code}'
                      AND EXISTS (SELECT 1 FROM "{table_name}" WHERE form_code = '{canonical_code}')
                    """
                )
            op.execute(
                f"""
                UPDATE "{table_name}"
                SET form_code = '{canonical_code}'
                WHERE form_code = '{old_code}'
                """
            )

    # 2. Item-table legacy column drops for Phase 1 forms
    _drop_if_exists("bid_document_icb_items", "material_name")
    _drop_if_exists("bid_document_icb_items", "item_code")
    _drop_if_exists("bid_document_lte_items", "material_name")
    _drop_if_exists("bid_document_ste_items", "material_name")
    _drop_if_exists("bid_document_techno_commercial_items", "material_name")
    _drop_if_exists("international_competitive_bidding_items", "material_name")
    _drop_if_exists("techno_commercial_tender_items", "material_name")
    _drop_if_exists("pqb_bid_document_items", "material_name")
    _drop_if_exists("eway_bill_items", "material_name")

    # 3. pqb_bid_documents
    op.add_column("pqb_bid_documents", sa.Column("total_no_corrigendum_issued", sa.Integer(), nullable=True))
    op.execute("UPDATE pqb_bid_documents SET total_no_corrigendum_issued = total_corrigendum_issued WHERE total_no_corrigendum_issued IS NULL")
    _drop_if_exists("pqb_bid_documents", "total_corrigendum_issued")

    # 4. corrigendums
    op.add_column("corrigendums", sa.Column("against_ref_no", sa.String(length=100), nullable=True))
    op.add_column("corrigendums", sa.Column("ref_title", sa.String(length=255), nullable=True))
    op.execute("UPDATE corrigendums SET against_ref_no = against_tender_no, ref_title = tender_title")
    _drop_if_exists("corrigendums", "against_tender_no")
    _drop_if_exists("corrigendums", "tender_title")

    # 5. notification_awards
    op.add_column("notification_awards", sa.Column("gst_pct", sa.Numeric(10, 2), nullable=True))
    op.add_column("notification_awards", sa.Column("total_net_amount", sa.Numeric(15, 2), nullable=True))
    op.add_column("notification_awards", sa.Column("gst_amount", sa.Numeric(15, 2), nullable=True))
    op.add_column("notification_awards", sa.Column("total_gross_amount", sa.Numeric(15, 2), nullable=True))

    # 6. project_steps nullability alignment
    op.alter_column("project_steps", "step_number", existing_type=sa.Integer(), nullable=True)
    op.alter_column("project_steps", "description", existing_type=sa.Text(), nullable=True)

    # 7. customer_queries & items
    op.add_column("customer_queries", sa.Column("customer_name", sa.String(length=255), nullable=True))
    op.add_column("customer_queries", sa.Column("query_date", sa.Date(), nullable=True))
    op.execute("UPDATE customer_queries SET query_date = COALESCE(qo_date, CURRENT_DATE)")
    op.alter_column("customer_queries", "query_date", existing_type=sa.Date(), nullable=False)
    _drop_if_exists("customer_queries", "qo_date")

    op.add_column("customer_query_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("customer_query_items", sa.Column("description", sa.String(length=500), nullable=True))
    op.execute("UPDATE customer_query_items SET description = COALESCE(material_name, '')")
    op.alter_column("customer_query_items", "description", existing_type=sa.String(length=500), nullable=False)
    _drop_if_exists("customer_query_items", "material_name")

    # 8. quotation_requests & items
    op.add_column("quotation_requests", sa.Column("supplier_name", sa.String(length=255), nullable=True))
    op.add_column("quotation_requests", sa.Column("request_date", sa.Date(), nullable=True))
    op.execute("UPDATE quotation_requests SET request_date = COALESCE(quotation_requested_date, CURRENT_DATE)")
    op.alter_column("quotation_requests", "request_date", existing_type=sa.Date(), nullable=False)
    _drop_if_exists("quotation_requests", "quotation_requested_date")

    op.add_column("quotation_request_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("quotation_request_items", sa.Column("description", sa.String(length=500), nullable=True))
    op.execute("UPDATE quotation_request_items SET description = COALESCE(material_name, '')")
    op.alter_column("quotation_request_items", "description", existing_type=sa.String(length=500), nullable=False)
    _drop_if_exists("quotation_request_items", "material_name")

    # 9. cost_sheet_items
    op.add_column("cost_sheet_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("cost_sheet_items", sa.Column("description", sa.String(length=500), nullable=True))
    op.execute("UPDATE cost_sheet_items SET description = COALESCE(item_description, '')")
    op.alter_column("cost_sheet_items", "description", existing_type=sa.String(length=500), nullable=False)
    _drop_if_exists("cost_sheet_items", "item_description")

    # 10. supplier_quotations & items
    op.add_column("supplier_quotations", sa.Column("quotation_no", sa.String(length=100), nullable=True))
    op.add_column("supplier_quotations", sa.Column("quotation_validity", sa.String(length=100), nullable=True))
    op.execute("UPDATE supplier_quotations SET quotation_no = COALESCE(quotation_number, ''), quotation_validity = validity")
    op.alter_column("supplier_quotations", "quotation_no", existing_type=sa.String(length=100), nullable=False)
    _drop_if_exists("supplier_quotations", "quotation_number")
    _drop_if_exists("supplier_quotations", "validity")

    op.add_column("supplier_quotation_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.execute("UPDATE supplier_quotation_items SET hsn_sac = hsn_code, description = COALESCE(description, material_name, '')")
    op.alter_column("supplier_quotation_items", "description", existing_type=sa.String(length=500), nullable=False)
    _drop_if_exists("supplier_quotation_items", "material_name")
    _drop_if_exists("supplier_quotation_items", "net_amount")
    _drop_if_exists("supplier_quotation_items", "hsn_code")

    # 11. customer_quotations & items
    op.add_column("customer_quotations", sa.Column("customer_name", sa.String(length=255), nullable=True))
    op.add_column("customer_quotations", sa.Column("quotation_no", sa.String(length=100), nullable=True))
    op.add_column("customer_quotations", sa.Column("quotation_validity", sa.String(length=100), nullable=True))
    op.execute("UPDATE customer_quotations SET quotation_no = COALESCE(quotation_number, qo_number), quotation_validity = validity")
    _drop_if_exists("customer_quotations", "qo_number")
    _drop_if_exists("customer_quotations", "quotation_number")
    _drop_if_exists("customer_quotations", "validity")

    op.add_column("customer_quotation_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("customer_quotation_items", sa.Column("description", sa.String(length=500), nullable=True))
    op.add_column("customer_quotation_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.add_column("customer_quotation_items", sa.Column("total_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE customer_quotation_items SET description = COALESCE(material_name, ''), total_amount = net_amount")
    op.alter_column("customer_quotation_items", "description", existing_type=sa.String(length=500), nullable=False)
    _drop_if_exists("customer_quotation_items", "material_name")
    _drop_if_exists("customer_quotation_items", "net_amount")

    # 12. customer_tenders & items
    op.add_column("customer_tenders", sa.Column("customer_name", sa.String(length=255), nullable=True))
    op.add_column("customer_tenders", sa.Column("tender_no", sa.String(length=100), nullable=True))
    op.add_column("customer_tenders", sa.Column("tender_issue_date", sa.DateTime(), nullable=True))
    op.execute("UPDATE customer_tenders SET tender_no = COALESCE(tender_number, ''), tender_issue_date = tender_date")
    op.alter_column("customer_tenders", "tender_no", existing_type=sa.String(length=100), nullable=False)
    _drop_if_exists("customer_tenders", "tender_number")
    _drop_if_exists("customer_tenders", "tender_date")

    op.add_column("customer_tender_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("customer_tender_items", sa.Column("unit", sa.String(length=50), nullable=True))

    # 13. purchase_orders & items
    op.add_column("purchase_orders", sa.Column("customer_name", sa.String(length=255), nullable=True))
    op.add_column("purchase_orders", sa.Column("po_no", sa.String(length=100), nullable=True))
    op.add_column("purchase_orders", sa.Column("gst_rate_pct", sa.Numeric(5, 2), nullable=True))
    op.add_column("purchase_orders", sa.Column("delivery_terms", sa.String(length=100), nullable=True))
    op.execute("UPDATE purchase_orders SET po_no = COALESCE(po_number, ''), gst_rate_pct = gst_rate, delivery_terms = delivery_term")
    op.alter_column("purchase_orders", "po_no", existing_type=sa.String(length=100), nullable=False)
    _drop_if_exists("purchase_orders", "po_number")
    _drop_if_exists("purchase_orders", "gst_rate")
    _drop_if_exists("purchase_orders", "delivery_term")

    op.add_column("purchase_order_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("purchase_order_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.add_column("purchase_order_items", sa.Column("total_price", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE purchase_order_items SET hsn_sac = hsn_code, total_price = net_amount, description = COALESCE(description, material_name)")
    _drop_if_exists("purchase_order_items", "hsn_code")
    _drop_if_exists("purchase_order_items", "material_name")
    _drop_if_exists("purchase_order_items", "net_amount")

    # 14. bid_submissions & items
    op.add_column("bid_submissions", sa.Column("customer_name", sa.String(length=255), nullable=True))
    op.add_column("bid_submissions", sa.Column("tender_no", sa.String(length=100), nullable=True))
    op.add_column("bid_submissions", sa.Column("total_no_corrigendum_issued", sa.Integer(), nullable=True))
    op.add_column("bid_submissions", sa.Column("bid_submission_date", sa.DateTime(), nullable=True))
    op.add_column("bid_submissions", sa.Column("delivery_terms", sa.String(length=100), nullable=True))
    op.add_column("bid_submissions", sa.Column("bid_validity", sa.String(length=100), nullable=True))
    op.add_column("bid_submissions", sa.Column("payment_terms", sa.String(length=255), nullable=True))
    op.add_column("bid_submissions", sa.Column("gst_pct", sa.Numeric(10, 2), nullable=True))
    op.add_column("bid_submissions", sa.Column("total_net_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("bid_submissions", sa.Column("gst_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("bid_submissions", sa.Column("total_gross_amount", sa.Numeric(18, 2), nullable=True))
    op.execute(
        """
        UPDATE bid_submissions
        SET tender_no = COALESCE(tender_number, ''),
            bid_submission_date = submission_date,
            delivery_terms = delivery_term,
            payment_terms = payment_term,
            bid_validity = validity,
            gst_pct = gst_rate
        """
    )
    op.alter_column("bid_submissions", "tender_no", existing_type=sa.String(length=100), nullable=False)
    _drop_if_exists("bid_submissions", "submission_date")
    _drop_if_exists("bid_submissions", "delivery_term")
    _drop_if_exists("bid_submissions", "payment_term")
    _drop_if_exists("bid_submissions", "validity")
    _drop_if_exists("bid_submissions", "gst_rate")
    _drop_if_exists("bid_submissions", "tender_number")

    op.add_column("bid_submission_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("bid_submission_items", sa.Column("total_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE bid_submission_items SET total_amount = net_total")
    _drop_if_exists("bid_submission_items", "net_total")

    # 15. supplier_order_confirmations & items
    op.add_column("supplier_order_confirmations", sa.Column("supplier_name", sa.String(length=255), nullable=True))
    op.add_column("supplier_order_confirmations", sa.Column("order_confirmation_no", sa.String(length=100), nullable=True))
    op.add_column("supplier_order_confirmations", sa.Column("incoterms", sa.String(length=100), nullable=True))
    op.execute("UPDATE supplier_order_confirmations SET order_confirmation_no = COALESCE(ref_no, ''), incoterms = shipping_terms")
    op.alter_column("supplier_order_confirmations", "order_confirmation_no", existing_type=sa.String(length=100), nullable=False)
    _drop_if_exists("supplier_order_confirmations", "ref_no")
    _drop_if_exists("supplier_order_confirmations", "shipping_terms")

    op.add_column("supplier_order_confirmation_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("supplier_order_confirmation_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.add_column("supplier_order_confirmation_items", sa.Column("total_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE supplier_order_confirmation_items SET hsn_sac = hsn_code, total_amount = net_amount, description = COALESCE(description, material_name)")
    _drop_if_exists("supplier_order_confirmation_items", "material_name")
    _drop_if_exists("supplier_order_confirmation_items", "hsn_code")
    _drop_if_exists("supplier_order_confirmation_items", "net_amount")

    # 16. supplier_proforma_invoices & items
    op.add_column("supplier_proforma_invoices", sa.Column("supplier_name", sa.String(length=255), nullable=True))
    op.add_column("supplier_proforma_invoices", sa.Column("incoterms", sa.String(length=100), nullable=True))
    op.execute("UPDATE supplier_proforma_invoices SET incoterms = delivery_terms")
    _drop_if_exists("supplier_proforma_invoices", "delivery_terms")

    op.add_column("supplier_proforma_invoice_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("supplier_proforma_invoice_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.add_column("supplier_proforma_invoice_items", sa.Column("total_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE supplier_proforma_invoice_items SET hsn_sac = hsn_code, total_amount = net_amount, description = COALESCE(description, material_name)")
    _drop_if_exists("supplier_proforma_invoice_items", "material_name")
    _drop_if_exists("supplier_proforma_invoice_items", "hsn_code")
    _drop_if_exists("supplier_proforma_invoice_items", "net_amount")

    # 17. supplier_invoices & items
    op.add_column("supplier_invoices", sa.Column("supplier_name", sa.String(length=255), nullable=True))
    op.add_column("supplier_invoices", sa.Column("incoterms", sa.String(length=100), nullable=True))
    op.execute("UPDATE supplier_invoices SET incoterms = delivery_terms")
    _drop_if_exists("supplier_invoices", "delivery_terms")

    op.add_column("supplier_invoice_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("supplier_invoice_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.add_column("supplier_invoice_items", sa.Column("total_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE supplier_invoice_items SET hsn_sac = hsn_code, total_amount = net_amount, description = COALESCE(description, material_name)")
    _drop_if_exists("supplier_invoice_items", "material_name")
    _drop_if_exists("supplier_invoice_items", "hsn_code")
    _drop_if_exists("supplier_invoice_items", "net_amount")

    # 18. supplier_packing_lists & items
    op.add_column("supplier_packing_lists", sa.Column("net_weight", sa.Numeric(18, 3), nullable=True))
    op.add_column("supplier_packing_lists", sa.Column("gross_weight", sa.Numeric(18, 3), nullable=True))
    op.add_column("supplier_packing_lists", sa.Column("total_no_packages", sa.Integer(), nullable=True))
    op.execute("UPDATE supplier_packing_lists SET net_weight = weight, gross_weight = total_weight")
    _drop_if_exists("supplier_packing_lists", "weight")
    _drop_if_exists("supplier_packing_lists", "total_weight")

    op.add_column("supplier_packing_list_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("supplier_packing_list_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.execute("UPDATE supplier_packing_list_items SET hsn_sac = hsn_code, description = COALESCE(description, material_name)")
    op.alter_column("supplier_packing_list_items", "unit_price", existing_type=sa.Numeric(18, 2), nullable=True)
    op.alter_column("supplier_packing_list_items", "quantity", existing_type=sa.Numeric(18, 3), nullable=True)
    _drop_if_exists("supplier_packing_list_items", "material_name")
    _drop_if_exists("supplier_packing_list_items", "hsn_code")
    _drop_if_exists("supplier_packing_list_items", "net_amount")
    _drop_if_exists("supplier_packing_list_items", "weight")

    # 19. supplier_payments
    op.add_column("supplier_payments", sa.Column("payment_pct", sa.Numeric(18, 2), nullable=True))
    op.add_column("supplier_payments", sa.Column("total_contract_value", sa.Numeric(18, 2), nullable=True))
    op.add_column("supplier_payments", sa.Column("payment_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("supplier_payments", sa.Column("reference_no", sa.Text(), nullable=True))
    op.add_column("supplier_payments", sa.Column("eur_to_inr_rate", sa.Numeric(18, 2), nullable=True))
    op.add_column("supplier_payments", sa.Column("payment_amount_inr", sa.Numeric(18, 2), nullable=True))
    op.execute(
        """
        UPDATE supplier_payments
        SET payment_pct = payment_percentage,
            total_contract_value = total_supplier_value,
            payment_amount = COALESCE(amount_paid, 0),
            reference_no = transaction_details,
            eur_to_inr_rate = ROUND(exchange_rate, 2),
            payment_amount_inr = total_with_exchange
        """
    )
    op.alter_column("supplier_payments", "payment_amount", existing_type=sa.Numeric(18, 2), nullable=False)
    _drop_if_exists("supplier_payments", "transaction_details")
    _drop_if_exists("supplier_payments", "payment_percentage")
    _drop_if_exists("supplier_payments", "total_supplier_value")
    _drop_if_exists("supplier_payments", "amount_paid")
    _drop_if_exists("supplier_payments", "exchange_rate")
    _drop_if_exists("supplier_payments", "total_with_exchange")
    _drop_if_exists("supplier_payments", "total_with_bank_charges")

    # 20. bills_of_entry (backfill from import_logistics & customs_clearances before dropping columns)
    op.add_column("bills_of_entry", sa.Column("logistic_mode", sa.String(length=100), nullable=True))
    op.add_column("bills_of_entry", sa.Column("shipment_date", sa.Date(), nullable=True))
    op.add_column("bills_of_entry", sa.Column("awb_bl_no", sa.String(length=100), nullable=True))
    op.add_column("bills_of_entry", sa.Column("flight_vessel_name", sa.String(length=255), nullable=True))
    op.add_column("bills_of_entry", sa.Column("flight_vessel_no", sa.String(length=100), nullable=True))
    op.add_column("bills_of_entry", sa.Column("port_loading", sa.String(length=255), nullable=True))
    op.add_column("bills_of_entry", sa.Column("port_discharge", sa.String(length=255), nullable=True))
    op.add_column("bills_of_entry", sa.Column("boe_filing_date", sa.Date(), nullable=True))
    op.add_column("bills_of_entry", sa.Column("basic_custom_duty_bcd", sa.Numeric(18, 2), nullable=True))
    op.add_column("bills_of_entry", sa.Column("duty_paid_date", sa.Date(), nullable=True))
    op.add_column("bills_of_entry", sa.Column("challan_no", sa.String(length=100), nullable=True))
    op.add_column("bills_of_entry", sa.Column("payment_ref_no", sa.String(length=255), nullable=True))
    op.add_column("bills_of_entry", sa.Column("customs_location", sa.String(length=255), nullable=True))
    op.add_column("bills_of_entry", sa.Column("cfs_name", sa.String(length=255), nullable=True))
    op.execute("UPDATE bills_of_entry SET boe_filing_date = date, basic_custom_duty_bcd = bcd")
    op.execute(
        """
        UPDATE bills_of_entry b
        SET logistic_mode = il.logistic_type,
            shipment_date = il.date,
            awb_bl_no = COALESCE(il.airway_bill_no, il.bill_of_lading_no),
            flight_vessel_name = COALESCE(il.flight_name, il.vessel_name),
            flight_vessel_no = COALESCE(il.flight_no, il.voyage_no),
            port_loading = COALESCE(il.airport_of_loading, il.port_of_loading),
            port_discharge = il.port_of_discharge
        FROM (
            SELECT DISTINCT ON (project_id) *
            FROM import_logistics
            ORDER BY project_id, id DESC
        ) il
        WHERE b.project_id = il.project_id
        """
    )
    op.execute(
        """
        UPDATE bills_of_entry b
        SET duty_paid_date = cc.duty_paid_date,
            challan_no = cc.challan_no,
            payment_ref_no = cc.transaction_ref_no,
            customs_location = cc.customs_location,
            cfs_name = cc.cfs_name
        FROM (
            SELECT DISTINCT ON (project_id) *
            FROM customs_clearances
            ORDER BY project_id, id DESC
        ) cc
        WHERE b.project_id = cc.project_id
        """
    )
    op.alter_column("bills_of_entry", "bill_of_entry_no", existing_type=sa.String(length=100), nullable=True)
    _drop_if_exists("bills_of_entry", "bcd")
    _drop_if_exists("bills_of_entry", "date")

    # 21. import_logistics
    op.add_column("import_logistics", sa.Column("transportation_mode", sa.String(length=50), nullable=True))
    op.add_column("import_logistics", sa.Column("lr_rr_awb_no", sa.String(length=100), nullable=True))
    op.add_column("import_logistics", sa.Column("lr_rr_awb_date", sa.Date(), nullable=True))
    op.add_column("import_logistics", sa.Column("from_location", sa.String(length=255), nullable=True))
    op.add_column("import_logistics", sa.Column("to_location", sa.String(length=255), nullable=True))
    op.add_column("import_logistics", sa.Column("total_transportation_charges", sa.Numeric(18, 2), nullable=True))
    op.execute(
        """
        UPDATE import_logistics
        SET transportation_mode = COALESCE(logistic_type, 'Sea'),
            lr_rr_awb_date = COALESCE(date, CURRENT_DATE),
            lr_rr_awb_no = COALESCE(airway_bill_no, bill_of_lading_no),
            from_location = COALESCE(airport_of_loading, port_of_loading),
            to_location = port_of_discharge
        """
    )
    op.alter_column("import_logistics", "transportation_mode", existing_type=sa.String(length=50), nullable=False)
    op.alter_column("import_logistics", "lr_rr_awb_date", existing_type=sa.Date(), nullable=False)
    for col in (
        "logistic_type",
        "flight_name",
        "airport_of_loading",
        "port_of_discharge",
        "date",
        "airway_bill_no",
        "flight_no",
        "bill_of_lading_no",
        "vessel_name",
        "voyage_no",
        "port_of_loading",
    ):
        _drop_if_exists("import_logistics", col)

    # 22. transport_details
    op.add_column("transport_details", sa.Column("transportation_mode", sa.String(length=50), nullable=True))
    op.add_column("transport_details", sa.Column("lr_rr_awb_no", sa.String(length=100), nullable=True))
    op.add_column("transport_details", sa.Column("lr_rr_awb_date", sa.Date(), nullable=True))
    op.add_column("transport_details", sa.Column("total_transportation_charges", sa.Numeric(18, 2), nullable=True))
    op.execute(
        """
        UPDATE transport_details
        SET transportation_mode = COALESCE(transport_mode, 'Road'),
            lr_rr_awb_no = COALESCE(lr_no, rr_no, awb_no),
            lr_rr_awb_date = COALESCE(date, CURRENT_DATE),
            total_transportation_charges = transport_charges
        """
    )
    op.alter_column("transport_details", "transportation_mode", existing_type=sa.String(length=50), nullable=False)
    op.alter_column("transport_details", "lr_rr_awb_date", existing_type=sa.Date(), nullable=False)
    for col in ("transport_charges", "transport_mode", "lr_no", "date", "rr_no", "awb_no"):
        _drop_if_exists("transport_details", col)

    # 23. customs_clearances & customs_clearance_items
    op.add_column("customs_clearances", sa.Column("freight_forwarder_name", sa.String(length=255), nullable=True))
    op.add_column("customs_clearances", sa.Column("invoice_no", sa.String(length=100), nullable=True))
    op.add_column("customs_clearances", sa.Column("invoice_date", sa.Date(), nullable=True))
    op.add_column("customs_clearances", sa.Column("invoice_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("customs_clearances", sa.Column("payment_date", sa.Date(), nullable=True))
    op.add_column("customs_clearances", sa.Column("payment_amount", sa.Numeric(18, 2), nullable=True))
    op.execute(
        """
        UPDATE customs_clearances
        SET freight_forwarder_name = cha_name,
            invoice_no = bill_of_entry_no,
            invoice_date = boe_date,
            invoice_amount = total_customs_amount,
            payment_date = duty_paid_date,
            payment_amount = duty_amount
        """
    )
    op.alter_column("customs_clearances", "cha_name", existing_type=sa.String(length=255), nullable=True)
    for col in (
        "duty_paid_date",
        "cfs_name",
        "duty_amount",
        "igst_amount",
        "other_customs_charges",
        "bill_of_entry_no",
        "boe_date",
        "customs_location",
        "challan_no",
        "transaction_ref_no",
        "total_customs_amount",
    ):
        _drop_if_exists("customs_clearances", col)

    op.create_table(
        "customs_clearance_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customs_clearance_id", sa.Integer(), sa.ForeignKey("customs_clearances.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sr_no", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_customs_clearance_items_customs_clearance_id", "customs_clearance_items", ["customs_clearance_id"])

    # 24. customer_payments
    op.add_column("customer_payments", sa.Column("payment_against_invoice_no", sa.String(length=100), nullable=True))
    op.add_column("customer_payments", sa.Column("payment_received", sa.Numeric(18, 2), nullable=True))
    op.add_column("customer_payments", sa.Column("payment_received_date", sa.Date(), nullable=True))
    op.add_column("customer_payments", sa.Column("ld_deducted", sa.Numeric(18, 2), nullable=True))
    op.add_column("customer_payments", sa.Column("tds_deducted", sa.Numeric(18, 2), nullable=True))
    op.add_column("customer_payments", sa.Column("balance_amount", sa.Numeric(18, 2), nullable=True))
    op.execute(
        """
        UPDATE customer_payments
        SET payment_against_invoice_no = COALESCE(invoice_no, ''),
            payment_received = COALESCE(payment_amount, 0),
            payment_received_date = COALESCE(payment_date, CURRENT_DATE),
            ld_deducted = ld,
            tds_deducted = tds,
            balance_amount = CASE
                WHEN invoice_value IS NOT NULL THEN GREATEST(invoice_value - COALESCE(payment_amount, 0) - COALESCE(tds, 0) - COALESCE(ld, 0), 0)
                ELSE NULL
            END
        """
    )
    op.alter_column("customer_payments", "payment_against_invoice_no", existing_type=sa.String(length=100), nullable=False)
    op.alter_column("customer_payments", "payment_received", existing_type=sa.Numeric(18, 2), nullable=False)
    op.alter_column("customer_payments", "payment_received_date", existing_type=sa.Date(), nullable=False)
    for col in ("payment_amount", "payment_date", "tds", "invoice_no", "ld"):
        _drop_if_exists("customer_payments", col)

    # 25. delivery_challans & items
    op.add_column("delivery_challans", sa.Column("gst_pct", sa.Numeric(18, 2), nullable=True))
    op.add_column("delivery_challans", sa.Column("total_net_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("delivery_challans", sa.Column("total_gross_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE delivery_challans SET gst_pct = gst_rate, total_gross_amount = net_total")
    _drop_if_exists("delivery_challans", "gst_rate")
    _drop_if_exists("delivery_challans", "net_total")

    op.add_column("delivery_challan_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("delivery_challan_items", sa.Column("description", sa.String(length=500), nullable=True))
    op.add_column("delivery_challan_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.add_column("delivery_challan_items", sa.Column("total_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE delivery_challan_items SET description = COALESCE(material_name, ''), hsn_sac = hsn_code, total_amount = COALESCE(net_amount, 0)")
    op.alter_column("delivery_challan_items", "description", existing_type=sa.String(length=500), nullable=False)
    op.alter_column("delivery_challan_items", "total_amount", existing_type=sa.Numeric(18, 2), nullable=False)
    op.alter_column("delivery_challan_items", "quantity", existing_type=sa.Numeric(18, 3), nullable=True)
    _drop_if_exists("delivery_challan_items", "material_name")
    _drop_if_exists("delivery_challan_items", "hsn_code")
    _drop_if_exists("delivery_challan_items", "net_amount")

    # 26. customer_delivery_packing_lists & items
    op.add_column("customer_delivery_packing_lists", sa.Column("total_no_packages", sa.Integer(), nullable=True))
    op.execute("UPDATE customer_delivery_packing_lists SET total_no_packages = total_no_of_packs")
    _drop_if_exists("customer_delivery_packing_lists", "total_no_of_packs")

    op.add_column("customer_delivery_packing_list_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("customer_delivery_packing_list_items", sa.Column("description", sa.String(length=500), nullable=True))
    op.add_column("customer_delivery_packing_list_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.add_column("customer_delivery_packing_list_items", sa.Column("unit_weight", sa.Numeric(18, 3), nullable=True))
    op.add_column("customer_delivery_packing_list_items", sa.Column("total_weight", sa.Numeric(18, 3), nullable=True))
    op.execute("UPDATE customer_delivery_packing_list_items SET description = COALESCE(material_name, ''), hsn_sac = hsn_code, total_weight = weight")
    op.alter_column("customer_delivery_packing_list_items", "description", existing_type=sa.String(length=500), nullable=False)
    op.alter_column("customer_delivery_packing_list_items", "quantity", existing_type=sa.Numeric(18, 3), nullable=True)
    _drop_if_exists("customer_delivery_packing_list_items", "material_name")
    _drop_if_exists("customer_delivery_packing_list_items", "hsn_code")
    _drop_if_exists("customer_delivery_packing_list_items", "weight")

    # 27. customer_delivery_invoices & items
    op.add_column("customer_delivery_invoices", sa.Column("customer_name", sa.String(length=255), nullable=True))
    op.add_column("customer_delivery_invoices", sa.Column("gst_pct", sa.Numeric(18, 2), nullable=True))
    op.add_column("customer_delivery_invoices", sa.Column("total_net_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column("customer_delivery_invoices", sa.Column("total_gross_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE customer_delivery_invoices SET gst_pct = gst_rate, total_gross_amount = net_total")
    _drop_if_exists("customer_delivery_invoices", "gst_rate")
    _drop_if_exists("customer_delivery_invoices", "net_total")

    op.add_column("customer_delivery_invoice_items", sa.Column("sr_no", sa.Integer(), nullable=True))
    op.add_column("customer_delivery_invoice_items", sa.Column("description", sa.String(length=500), nullable=True))
    op.add_column("customer_delivery_invoice_items", sa.Column("hsn_sac", sa.String(length=50), nullable=True))
    op.add_column("customer_delivery_invoice_items", sa.Column("total_amount", sa.Numeric(18, 2), nullable=True))
    op.execute("UPDATE customer_delivery_invoice_items SET description = COALESCE(material_name, ''), hsn_sac = hsn_code, total_amount = COALESCE(net_amount, 0)")
    op.alter_column("customer_delivery_invoice_items", "description", existing_type=sa.String(length=500), nullable=False)
    op.alter_column("customer_delivery_invoice_items", "total_amount", existing_type=sa.Numeric(18, 2), nullable=False)
    _drop_if_exists("customer_delivery_invoice_items", "material_name")
    _drop_if_exists("customer_delivery_invoice_items", "hsn_code")
    _drop_if_exists("customer_delivery_invoice_items", "net_amount")


def downgrade():
    # Minimal structural downgrade notice: re-adds previous column names without recreating dropped historical layouts
    op.drop_index("ix_customs_clearance_items_customs_clearance_id", table_name="customs_clearance_items")
    op.drop_table("customs_clearance_items")
    raise NotImplementedError("Downgrade from canonical schema standardization requires restoring from DB backup.")
