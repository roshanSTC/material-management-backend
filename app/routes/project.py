from flask import current_app, jsonify
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.extensions.database import db
from app.models import (
    BidDocumentLte,
    BidDocumentTechnoCommercial,
    BidSubmission,
    BillOfEntry,
    ConsultancyInvoice,
    Corrigendum,
    CostSheet,
    CustomerDeliveryInvoice,
    CustomerDeliveryPackingList,
    CustomerPayment,
    CustomerQuery,
    CustomerQuotation,
    CustomerTender,
    CustomsClearance,
    DeliveryChallan,
    EWayBill,
    ExpressionOfInterest,
    LimitedTenderEnquiry,
    NotificationAward,
    PqbBidDocument,
    PreQualificationBid,
    PurchaseOrder,
    QuotationRequest,
    SupplierInvoice,
    SupplierOrderConfirmation,
    SupplierPackingList,
    SupplierPayment,
    SupplierProformaInvoice,
    SupplierQuotation,
    TechnoCommercialTender,
    TransportDetail,
    WarrantyCertificate,
)
from app.schemas.project import (
    ProjectCreateSchema,
    ProjectListResponseSchema,
    ProjectResponseSchema,
    ProjectSearchQuerySchema,
    ProjectSearchResponseSchema,
    ProjectUpdateSchema,
)
from app.services.project_service import (
    CustomerNotFoundError,
    ProjectNotFoundError,
    SupplierNotFoundError,
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

project_bp = Blueprint(
    "projects",
    __name__,
    url_prefix="/api/v1/projects",
    description="Project Management APIs",
)

STEP_NAMES = {
    1: "Customer Query",
    2: "Request Supplier Quotation",
    3: "Supplier Quotation",
    4: "Cost Sheet",
    5: "Quotation to Customer",
    6: "Customer Tender",
    7: "Bid Submission",
    8: "Purchase Order (PO)",
    9: "Order Confirmation to Supplier",
    10: "Supplier Invoice",
    11: "Material Delivery",
    12: "Customs Clearance",
    13: "Customer Invoice",
    14: "Customer Payment",
    15: "Payment to Supplier",
}

STEP_NEXT_ACTIONS = {
    1: "Request Supplier Quotation",
    2: "Supplier Quotation",
    3: "Cost Sheet",
    4: "Quotation to Customer",
    5: "Customer Tender",
    6: "Bid Submission",
    7: "Purchase Order (PO)",
    8: "Order Confirmation to Supplier",
    9: "Supplier Invoice",
    10: "Material Delivery",
    11: "Customs Clearance",
    12: "Customer Invoice",
    13: "Customer Payment",
    14: "Payment to Supplier",
}

LABEL_BY_KEY = {
    "pqb_closing_date_time": "PQB Closed",
    "pqb_closing_date": "PQB Closed",
    "closing_date_time": "Closing Date",
    "closing_date": "Closing Date",
    "submission_deadline": "Due Date",
    "due_date": "Due Date",
    "delivery_date": "Delivery Date",
    "expected_delivery_date": "Delivery Date",
    "target_delivery_date": "Delivery Date",
    "qo_date": "Query Date",
    "query_date": "Query Date",
    "quotation_requested_date": "RFQ Date",
    "rfq_date": "RFQ Date",
    "request_date": "RFQ Date",
    "quotation_date": "Quotation Date",
    "quote_date": "Quotation Date",
    "cost_sheet_date": "Cost Sheet Date",
    "po_date": "PO Date",
    "order_confirmation_date": "Confirmation Date",
    "proforma_invoice_date": "Proforma Date",
    "invoice_date": "Invoice Date",
    "delivery_challan_date": "Challan Date",
    "challan_date": "Challan Date",
    "packing_list_date": "Packing List Date",
    "payment_date": "Payment Date",
    "certificate_date": "Certificate Date",
    "boe_date": "BOE Date",
    "duty_paid_date": "Duty Paid Date",
    "dispatch_date": "Dispatch Date",
    "eway_bill_date": "E-Way Date",
    "bid_submission_date": "Submission Date",
    "submission_date": "Submission Date",
    "tender_date": "Tender Date",
    "tender_issue_date": "Tender Date",
    "pqb_issuing_date": "PQB Issue Date",
    "pqb_issue_date": "PQB Issue Date",
    "issue_date": "Issue Date",
}


def _get_project_margin_info(project_id):
    total_margin = None
    margin_percentage = None
    try:
        cost_sheet = (
            CostSheet.query.filter_by(project_id=project_id)
            .order_by(CostSheet.version_number.desc(), CostSheet.id.desc())
            .first()
        )
        if cost_sheet:
            output = cost_sheet.output
            if not output:
                from app.services.cost_sheet_service import calculate_cost_sheet
                from app.services.project_cost_sheet_service import _calculation_item
                output = calculate_cost_sheet(
                    global_params=cost_sheet.global_params or {},
                    items=[_calculation_item(item) for item in cost_sheet.items],
                )
            if isinstance(output, dict):
                col_totals = output.get("columnTotals", {})
                if isinstance(col_totals, dict) and col_totals.get("marginInr") is not None:
                    total_margin = col_totals["marginInr"]
                elif output.get("marginInr") is not None:
                    total_margin = output["marginInr"]

            # Margin percentage resolution
            margin_rate_raw = None
            gp = cost_sheet.global_params
            if isinstance(gp, dict):
                margin_rate_raw = (
                    gp.get("marginRate")
                    or gp.get("margin_rate")
                    or gp.get("marginPercent")
                    or gp.get("margin_percent")
                )
            if margin_rate_raw is None and isinstance(output, dict):
                out_gp = output.get("globalParams")
                if isinstance(out_gp, dict):
                    margin_rate_raw = (
                        out_gp.get("marginRate")
                        or out_gp.get("margin_rate")
                        or out_gp.get("marginPercent")
                        or out_gp.get("margin_percent")
                    )

            if margin_rate_raw is not None:
                try:
                    val = float(margin_rate_raw)
                    if 0 < val < 1.0:
                        pct = round(val * 100.0, 4)
                        margin_percentage = int(pct) if pct == int(pct) else pct
                    else:
                        margin_percentage = int(val) if val == int(val) else val
                except (ValueError, TypeError):
                    pass

            if margin_percentage is None and isinstance(output, dict):
                col_totals = output.get("columnTotals", {})
                if isinstance(col_totals, dict):
                    m_inr = col_totals.get("marginInr")
                    base_inr = col_totals.get("lessIgstInr") or col_totals.get("totalCostInr")
                    if m_inr is not None and base_inr:
                        try:
                            base_val = float(base_inr)
                            if base_val > 0:
                                pct = round((float(m_inr) / base_val) * 100.0, 2)
                                margin_percentage = int(pct) if pct == int(pct) else pct
                        except (ValueError, TypeError):
                            pass
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Failed to calculate margin info for project %s: %s", project_id, exc)
    return total_margin, margin_percentage


def _get_project_latest_items(project_id):
    """
    Returns (step_number, step_name, items_list) for the latest step of the project that contains items.
    Items list contains standardized dictionaries with:
      id, material_name, quantity, unit_price, net_amount, hsn_code, step_number, step_name
    """
    # Step 13: Customer Delivery Invoice / Challan / Packing List
    try:
        cdis = (
            CustomerDeliveryInvoice.query.filter_by(project_id=project_id)
            .order_by(CustomerDeliveryInvoice.id.desc())
            .all()
        )
        for cdi in cdis:
            if cdi.items:
                return 13, "Customer Invoice", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 13,
                        "step_name": "Customer Invoice",
                    }
                    for item in cdi.items
                ]

        dcs = (
            DeliveryChallan.query.filter_by(project_id=project_id)
            .order_by(DeliveryChallan.id.desc())
            .all()
        )
        for dc in dcs:
            if dc.items:
                return 13, "Customer Invoice", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 13,
                        "step_name": "Customer Invoice",
                    }
                    for item in dc.items
                ]

        cdpls = (
            CustomerDeliveryPackingList.query.filter_by(project_id=project_id)
            .order_by(CustomerDeliveryPackingList.id.desc())
            .all()
        )
        for cdpl in cdpls:
            if cdpl.items:
                return 13, "Customer Invoice", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": None,
                        "net_amount": None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 13,
                        "step_name": "Customer Invoice",
                    }
                    for item in cdpl.items
                ]
    except Exception:
        db.session.rollback()

    # Step 10: Supplier Invoice / Packing List / Proforma
    try:
        sis = (
            SupplierInvoice.query.filter_by(project_id=project_id)
            .order_by(SupplierInvoice.id.desc())
            .all()
        )
        for si in sis:
            if si.items:
                return 10, "Supplier Invoice", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 10,
                        "step_name": "Supplier Invoice",
                    }
                    for item in si.items
                ]

        spls = (
            SupplierPackingList.query.filter_by(project_id=project_id)
            .order_by(SupplierPackingList.id.desc())
            .all()
        )
        for spl in spls:
            if spl.items:
                return 10, "Supplier Invoice", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 10,
                        "step_name": "Supplier Invoice",
                    }
                    for item in spl.items
                ]

        spis = (
            SupplierProformaInvoice.query.filter_by(project_id=project_id)
            .order_by(SupplierProformaInvoice.id.desc())
            .all()
        )
        for spi in spis:
            if spi.items:
                return 10, "Supplier Invoice", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 10,
                        "step_name": "Supplier Invoice",
                    }
                    for item in spi.items
                ]
    except Exception:
        db.session.rollback()

    # Step 9: Order Confirmation to Supplier
    try:
        socs = (
            SupplierOrderConfirmation.query.filter_by(project_id=project_id)
            .order_by(SupplierOrderConfirmation.id.desc())
            .all()
        )
        for soc in socs:
            if soc.items:
                return 9, "Order Confirmation to Supplier", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 9,
                        "step_name": "Order Confirmation to Supplier",
                    }
                    for item in soc.items
                ]
    except Exception:
        db.session.rollback()

    # Step 8: Purchase Order (PO)
    try:
        pos = (
            PurchaseOrder.query.filter_by(project_id=project_id)
            .order_by(PurchaseOrder.id.desc())
            .all()
        )
        for po in pos:
            if po.items:
                return 8, "Purchase Order (PO)", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 8,
                        "step_name": "Purchase Order (PO)",
                    }
                    for item in po.items
                ]
    except Exception:
        db.session.rollback()

    # Step 7: Bid Submission
    try:
        bss = (
            BidSubmission.query.filter_by(project_id=project_id)
            .order_by(BidSubmission.id.desc())
            .all()
        )
        for bs in bss:
            if bs.items:
                return 7, "Bid Submission", [
                    {
                        "id": item.id,
                        "material_name": item.material_name or getattr(item, "description", None),
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_total) if getattr(item, "net_total", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_sac", None),
                        "step_number": 7,
                        "step_name": "Bid Submission",
                    }
                    for item in bs.items
                ]
    except Exception:
        db.session.rollback()

    # Step 6: Customer Tender
    try:
        cts = (
            CustomerTender.query.filter_by(project_id=project_id)
            .order_by(CustomerTender.id.desc())
            .all()
        )
        for ct in cts:
            if ct.items:
                return 6, "Customer Tender", [
                    {
                        "id": item.id,
                        "material_name": item.material_name or getattr(item, "description", None),
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": None,
                        "net_amount": None,
                        "hsn_code": None,
                        "step_number": 6,
                        "step_name": "Customer Tender",
                    }
                    for item in ct.items
                ]
    except Exception:
        db.session.rollback()

    # Step 5: Customer Quotation
    try:
        cqs = (
            CustomerQuotation.query.filter_by(project_id=project_id)
            .order_by(CustomerQuotation.id.desc())
            .all()
        )
        for cq in cqs:
            if cq.items:
                return 5, "Quotation to Customer", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": None,
                        "step_number": 5,
                        "step_name": "Quotation to Customer",
                    }
                    for item in cq.items
                ]
    except Exception:
        db.session.rollback()

    # Step 4: Cost Sheet
    try:
        css = (
            CostSheet.query.filter_by(project_id=project_id)
            .order_by(CostSheet.version_number.desc(), CostSheet.id.desc())
            .all()
        )
        for cs in css:
            if cs.items:
                return 4, "Cost Sheet", [
                    {
                        "id": item.id,
                        "material_name": getattr(item, "item_description", None),
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.price_per_unit_eur) if getattr(item, "price_per_unit_eur", None) is not None else None,
                        "net_amount": None,
                        "hsn_code": None,
                        "step_number": 4,
                        "step_name": "Cost Sheet",
                    }
                    for item in cs.items
                ]
    except Exception:
        db.session.rollback()

    # Step 3: Supplier Quotation
    try:
        sqs = (
            SupplierQuotation.query.filter_by(project_id=project_id)
            .order_by(SupplierQuotation.id.desc())
            .all()
        )
        for sq in sqs:
            if sq.items:
                return 3, "Supplier Quotation", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": float(item.unit_price) if getattr(item, "unit_price", None) is not None else None,
                        "net_amount": float(item.net_amount) if getattr(item, "net_amount", None) is not None else None,
                        "hsn_code": getattr(item, "hsn_code", None),
                        "step_number": 3,
                        "step_name": "Supplier Quotation",
                    }
                    for item in sq.items
                ]
    except Exception:
        db.session.rollback()

    # Step 2: Request Supplier Quotation (RFQ)
    try:
        qrs = (
            QuotationRequest.query.filter_by(project_id=project_id)
            .order_by(QuotationRequest.id.desc())
            .all()
        )
        for qr in qrs:
            if qr.items:
                return 2, "Request Supplier Quotation", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": None,
                        "net_amount": None,
                        "hsn_code": None,
                        "step_number": 2,
                        "step_name": "Request Supplier Quotation",
                    }
                    for item in qr.items
                ]
    except Exception:
        db.session.rollback()

    # Step 1: Customer Query
    try:
        c_queries = (
            CustomerQuery.query.filter_by(project_id=project_id)
            .order_by(CustomerQuery.id.desc())
            .all()
        )
        for c_query in c_queries:
            if c_query.items:
                return 1, "Customer Query", [
                    {
                        "id": item.id,
                        "material_name": item.material_name,
                        "quantity": float(item.quantity) if item.quantity is not None else None,
                        "unit_price": None,
                        "net_amount": None,
                        "hsn_code": None,
                        "step_number": 1,
                        "step_name": "Customer Query",
                    }
                    for item in c_query.items
                ]
    except Exception:
        db.session.rollback()

    return None, None, []


def _format_date_val(val):
    if not val:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "undefined"):
        return None
    return s


def _get_step_item_date(project, step):
    """
    Extracts (formatted_date, date_label) for the step, e.g.:
    - Customer Query: (qo_date, "Query Date")
    - Quotations: (quotation_date, "Quotation Date")
    - PQB: (pqb_closing_date_time, "PQB Closed")
    - Purchase Order: (po_date, "PO Date") or (delivery_date, "Delivery Date")
    - Invoices: (invoice_date, "Invoice Date")
    - Payments: (payment_date, "Payment Date")
    Explicitly does NOT use created_at / entry creation date.
    """
    if not step or not project:
        return None, None

    form_code = getattr(step, "form_code", None) or ""
    step_num = getattr(step, "step_number", None) or getattr(step, "step_order", None)
    step_data = getattr(step, "data", None)
    if isinstance(step_data, str):
        try:
            import json
            step_data = json.loads(step_data)
        except Exception:
            step_data = {}
    if not isinstance(step_data, dict):
        step_data = {}

    form_code_upper = form_code.upper()

    # 1. First check explicit business date keys in step.data (if step was saved via dynamic step API)
    if "PQB" in form_code_upper:
        priority_keys = [
            "pqb_closing_date_time", "pqb_closing_date", "closing_date_time", "closing_date",
            "submission_deadline", "pqb_issuing_date", "pqb_issue_date", "issue_date",
            "pqb_opening_date_time", "opening_date_time"
        ]
    elif "QUERY" in form_code_upper or step_num == 1:
        priority_keys = ["qo_date", "query_date", "date"]
    elif "RFQ" in form_code_upper or step_num == 2:
        priority_keys = ["quotation_requested_date", "rfq_date", "request_date", "date"]
    elif "QUOTATION" in form_code_upper or step_num in (3, 5):
        priority_keys = ["quotation_date", "quote_date", "valid_till", "validity_date", "date"]
    elif "COST_SHEET" in form_code_upper or step_num == 4:
        priority_keys = ["cost_sheet_date", "effective_date", "date"]
    elif "TENDER" in form_code_upper or step_num == 6:
        priority_keys = ["closing_date_time", "closing_date", "tender_date", "tender_issue_date", "opening_date_time", "date"]
    elif "BID" in form_code_upper or step_num == 7:
        priority_keys = ["bid_submission_date", "submission_date", "tender_issue_date", "bid_date", "date"]
    elif "ORDER_CONFIRMATION" in form_code_upper or step_num == 9:
        priority_keys = ["order_confirmation_date", "expected_delivery_date", "delivery_date", "date"]
    elif "PROFORMA" in form_code_upper:
        priority_keys = ["proforma_invoice_date", "invoice_date", "delivery_date", "date"]
    elif "INVOICE" in form_code_upper or step_num in (10, 13):
        priority_keys = ["invoice_date", "due_date", "date"]
    elif "PACKING" in form_code_upper:
        priority_keys = ["packing_list_date", "date"]
    elif "PAYMENT" in form_code_upper or step_num in (14, 15):
        priority_keys = ["payment_date", "date"]
    elif "CHALLAN" in form_code_upper:
        priority_keys = ["delivery_challan_date", "challan_date", "dispatch_date", "date"]
    elif "WARRANTY" in form_code_upper:
        priority_keys = ["certificate_date", "date"]
    elif "SHIPPING" in form_code_upper or "CLEARANCE" in form_code_upper or step_num in (11, 12):
        priority_keys = ["date", "bill_of_entry_date", "boe_date", "duty_paid_date"]
    elif "PURCHASE_ORDER" in form_code_upper or step_num == 8:
        priority_keys = ["po_date", "delivery_date", "due_date", "date"]
    else:
        priority_keys = [
            "due_date", "closing_date_time", "closing_date", "quotation_date",
            "invoice_date", "po_date", "payment_date", "date"
        ]

    for k in priority_keys:
        val = step_data.get(k)
        if val:
            formatted = _format_date_val(val)
            if formatted:
                label = LABEL_BY_KEY.get(k, "Step Date")
                return formatted, label

    # 2. Check relational database records on project
    try:
        if form_code_upper == "FORM_08_CUSTOMER_QUERY" or step_num == 1:
            cq = CustomerQuery.query.filter_by(project_id=project.id).order_by(CustomerQuery.id.desc()).first()
            if cq and getattr(cq, "qo_date", None):
                return _format_date_val(cq.qo_date), "Query Date"

        elif form_code_upper == "FORM_09_RFQ" or step_num == 2:
            rfq = QuotationRequest.query.filter_by(project_id=project.id).order_by(QuotationRequest.id.desc()).first()
            if rfq and getattr(rfq, "quotation_requested_date", None):
                return _format_date_val(rfq.quotation_requested_date), "RFQ Date"

        elif form_code_upper == "FORM_11_SUPPLIER_QUOTATION" or step_num == 3:
            sq = SupplierQuotation.query.filter_by(project_id=project.id).order_by(SupplierQuotation.id.desc()).first()
            if sq:
                if getattr(sq, "quotation_date", None):
                    return _format_date_val(sq.quotation_date), "Quotation Date"
                if getattr(sq, "valid_till", None):
                    return _format_date_val(sq.valid_till), "Valid Till"

        elif form_code_upper == "FORM_10_COST_SHEET" or step_num == 4:
            cs = CostSheet.query.filter_by(project_id=project.id).order_by(CostSheet.version_number.desc(), CostSheet.id.desc()).first()
            if cs:
                gp = cs.global_params if isinstance(cs.global_params, dict) else {}
                for k in ("date", "cost_sheet_date", "effective_date"):
                    if gp.get(k):
                        return _format_date_val(gp.get(k)), "Cost Sheet Date"

        elif form_code_upper == "FORM_12_CUSTOMER_QUOTATION" or step_num == 5:
            cq = CustomerQuotation.query.filter_by(project_id=project.id).order_by(CustomerQuotation.id.desc()).first()
            if cq and getattr(cq, "quotation_date", None):
                return _format_date_val(cq.quotation_date), "Quotation Date"

        elif form_code_upper == "FORM_13_PAC_TENDER" or step_num == 6:
            ct = CustomerTender.query.filter_by(project_id=project.id).order_by(CustomerTender.id.desc()).first()
            if ct:
                if getattr(ct, "closing_date_time", None):
                    return _format_date_val(ct.closing_date_time), "Closing Date"
                if getattr(ct, "tender_date", None):
                    return _format_date_val(ct.tender_date), "Tender Date"
                if getattr(ct, "opening_date_time", None):
                    return _format_date_val(ct.opening_date_time), "Opening Date"

        elif form_code_upper == "FORM_15_BID_DOCUMENT" or step_num == 7:
            bs = BidSubmission.query.filter_by(project_id=project.id).order_by(BidSubmission.id.desc()).first()
            if bs:
                if getattr(bs, "submission_date", None):
                    return _format_date_val(bs.submission_date), "Submission Date"
                if getattr(bs, "tender_issue_date", None):
                    return _format_date_val(bs.tender_issue_date), "Tender Date"

        elif form_code_upper == "FORM_14_PURCHASE_ORDER" or step_num == 8:
            po = PurchaseOrder.query.filter_by(project_id=project.id).order_by(PurchaseOrder.id.desc()).first()
            if po:
                if getattr(po, "delivery_date", None):
                    return _format_date_val(po.delivery_date), "Delivery Date"
                if getattr(po, "po_date", None):
                    return _format_date_val(po.po_date), "PO Date"

        elif form_code_upper == "FORM_16_ORDER_CONFIRMATION" or step_num == 9:
            soc = SupplierOrderConfirmation.query.filter_by(project_id=project.id).order_by(SupplierOrderConfirmation.id.desc()).first()
            if soc:
                if getattr(soc, "expected_delivery_date", None):
                    return _format_date_val(soc.expected_delivery_date), "Delivery Date"
                if getattr(soc, "order_confirmation_date", None):
                    return _format_date_val(soc.order_confirmation_date), "Confirmation Date"

        elif form_code_upper == "FORM_18_SUPPLIER_INVOICE" or step_num == 10:
            si = SupplierInvoice.query.filter_by(project_id=project.id).order_by(SupplierInvoice.id.desc()).first()
            if si:
                if getattr(si, "due_date", None):
                    return _format_date_val(si.due_date), "Due Date"
                if getattr(si, "invoice_date", None):
                    return _format_date_val(si.invoice_date), "Invoice Date"
            spi = SupplierProformaInvoice.query.filter_by(project_id=project.id).order_by(SupplierProformaInvoice.id.desc()).first()
            if spi and getattr(spi, "proforma_invoice_date", None):
                return _format_date_val(spi.proforma_invoice_date), "Proforma Date"

        elif form_code_upper == "FORM_17_PROFORMA_INVOICE":
            spi = SupplierProformaInvoice.query.filter_by(project_id=project.id).order_by(SupplierProformaInvoice.id.desc()).first()
            if spi and getattr(spi, "proforma_invoice_date", None):
                return _format_date_val(spi.proforma_invoice_date), "Proforma Date"

        elif form_code_upper == "FORM_19_SUPPLIER_PACKING_LIST":
            spl = SupplierPackingList.query.filter_by(project_id=project.id).order_by(SupplierPackingList.id.desc()).first()
            if spl and getattr(spl, "packing_list_date", None):
                return _format_date_val(spl.packing_list_date), "Packing List Date"

        elif form_code_upper == "FORM_20_PAYMENT_TO_SUPPLIER" or step_num == 15:
            sp = SupplierPayment.query.filter_by(project_id=project.id).order_by(SupplierPayment.id.desc()).first()
            if sp and getattr(sp, "payment_date", None):
                return _format_date_val(sp.payment_date), "Payment Date"

        elif form_code_upper == "FORM_22_PAYMENT_FROM_CUSTOMER" or step_num == 14:
            cp = CustomerPayment.query.filter_by(project_id=project.id).order_by(CustomerPayment.id.desc()).first()
            if cp:
                if getattr(cp, "payment_date", None):
                    return _format_date_val(cp.payment_date), "Payment Date"
                if getattr(cp, "invoice_date", None):
                    return _format_date_val(cp.invoice_date), "Invoice Date"

        elif form_code_upper == "FORM_23_WARRANTY_CERTIFICATE":
            wc = WarrantyCertificate.query.filter_by(project_id=project.id).order_by(WarrantyCertificate.id.desc()).first()
            if wc and getattr(wc, "certificate_date", None):
                return _format_date_val(wc.certificate_date), "Certificate Date"

        elif form_code_upper == "FORM_24_DELIVERY_CHALLAN":
            dc = DeliveryChallan.query.filter_by(project_id=project.id).order_by(DeliveryChallan.id.desc()).first()
            if dc and getattr(dc, "delivery_challan_date", None):
                return _format_date_val(dc.delivery_challan_date), "Challan Date"

        elif form_code_upper == "FORM_25_CUSTOMER_PACKING_LIST":
            cpl = CustomerDeliveryPackingList.query.filter_by(project_id=project.id).order_by(CustomerDeliveryPackingList.id.desc()).first()
            if cpl and getattr(cpl, "packing_list_date", None):
                return _format_date_val(cpl.packing_list_date), "Packing List Date"

        elif form_code_upper == "FORM_26_TAX_INVOICE_CUSTOMER" or step_num == 13:
            cdi = CustomerDeliveryInvoice.query.filter_by(project_id=project.id).order_by(CustomerDeliveryInvoice.id.desc()).first()
            if cdi:
                if getattr(cdi, "due_date", None):
                    return _format_date_val(cdi.due_date), "Due Date"
                if getattr(cdi, "invoice_date", None):
                    return _format_date_val(cdi.invoice_date), "Invoice Date"
            dc = DeliveryChallan.query.filter_by(project_id=project.id).order_by(DeliveryChallan.id.desc()).first()
            if dc and getattr(dc, "delivery_challan_date", None):
                return _format_date_val(dc.delivery_challan_date), "Challan Date"

        elif form_code_upper == "FORM_27_SHIPPING_CLEARANCE" or step_num == 11:
            boe = BillOfEntry.query.filter_by(project_id=project.id).order_by(BillOfEntry.id.desc()).first()
            if boe and getattr(boe, "date", None):
                return _format_date_val(boe.date), "BOE Date"

        elif form_code_upper == "FORM_28_FREIGHT_CHA" or step_num == 12:
            cc = CustomsClearance.query.filter_by(project_id=project.id).order_by(CustomsClearance.id.desc()).first()
            if cc:
                if getattr(cc, "duty_paid_date", None):
                    return _format_date_val(cc.duty_paid_date), "Duty Paid Date"
                if getattr(cc, "boe_date", None):
                    return _format_date_val(cc.boe_date), "BOE Date"

        elif form_code_upper == "FORM_01_PQB":
            pqb = PreQualificationBid.query.filter_by(project_id=project.id).order_by(PreQualificationBid.id.desc()).first()
            if pqb:
                if getattr(pqb, "pqb_closing_date_time", None):
                    return _format_date_val(pqb.pqb_closing_date_time), "PQB Closed"
                if getattr(pqb, "submission_deadline", None):
                    return _format_date_val(pqb.submission_deadline), "Submission Deadline"
                if getattr(pqb, "pqb_issuing_date", None):
                    return _format_date_val(pqb.pqb_issuing_date), "PQB Issue Date"

        elif form_code_upper == "FORM_02_PQB_BID_DOCUMENT":
            pbd = PqbBidDocument.query.filter_by(project_id=project.id).order_by(PqbBidDocument.id.desc()).first()
            if pbd:
                if getattr(pbd, "pqb_closing_date_time", None):
                    return _format_date_val(pbd.pqb_closing_date_time), "PQB Closed"
                if getattr(pbd, "pqb_issue_date", None):
                    return _format_date_val(pbd.pqb_issue_date), "PQB Issue Date"

        elif form_code_upper == "FORM_03_CORRIGENDUM":
            corr = Corrigendum.query.filter_by(project_id=project.id).order_by(Corrigendum.id.desc()).first()
            if corr and getattr(corr, "issue_date", None):
                return _format_date_val(corr.issue_date), "Issue Date"

        elif form_code_upper == "FORM_04_LTE":
            lte = LimitedTenderEnquiry.query.filter_by(project_id=project.id).order_by(LimitedTenderEnquiry.id.desc()).first()
            if lte:
                if getattr(lte, "closing_date_time", None):
                    return _format_date_val(lte.closing_date_time), "Closing Date"
                if getattr(lte, "issue_date", None):
                    return _format_date_val(lte.issue_date), "Issue Date"

        elif form_code_upper == "FORM_05_NAC":
            nac = NotificationAward.query.filter_by(project_id=project.id).order_by(NotificationAward.id.desc()).first()
            if nac:
                if getattr(nac, "nac_date", None):
                    return _format_date_val(nac.nac_date), "Award Date"

        elif form_code_upper == "FORM_06_CONSULTANCY_INVOICE":
            ci = ConsultancyInvoice.query.filter_by(project_id=project.id).order_by(ConsultancyInvoice.id.desc()).first()
            if ci and getattr(ci, "invoice_date", None):
                return _format_date_val(ci.invoice_date), "Invoice Date"

        elif form_code_upper == "FORM_07_EOI":
            eoi = ExpressionOfInterest.query.filter_by(project_id=project.id).order_by(ExpressionOfInterest.id.desc()).first()
            if eoi:
                if getattr(eoi, "closing_date", None):
                    return _format_date_val(eoi.closing_date), "Closing Date"
                if getattr(eoi, "issue_date", None):
                    return _format_date_val(eoi.issue_date), "Issue Date"

        elif form_code_upper == "FORM_29_BID_DOC_TECHNO_COMMERCIAL":
            bdtc = BidDocumentTechnoCommercial.query.filter_by(project_id=project.id).order_by(BidDocumentTechnoCommercial.id.desc()).first()
            if bdtc:
                if getattr(bdtc, "bid_submission_date", None):
                    return _format_date_val(bdtc.bid_submission_date), "Submission Date"
                if getattr(bdtc, "tender_issue_date", None):
                    return _format_date_val(bdtc.tender_issue_date), "Tender Date"

        elif form_code_upper == "FORM_30_TECHNO_COMMERCIAL_TENDER":
            tct = TechnoCommercialTender.query.filter(
                TechnoCommercialTender.project_id == project.id,
                TechnoCommercialTender.form_code.in_(["FORM_30_TECHNO_COMMERCIAL_TENDER", "FORM_30_TCT", "FORM_30"])
            ).order_by(TechnoCommercialTender.id.desc()).first()
            if tct:
                if getattr(tct, "bid_submission_due_date_time", None):
                    return _format_date_val(tct.bid_submission_due_date_time), "Due Date"
                if getattr(tct, "tender_issue_date", None):
                    return _format_date_val(tct.tender_issue_date), "Tender Date"

        elif form_code_upper in ("FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_STE"):
            ste = TechnoCommercialTender.query.filter(
                TechnoCommercialTender.project_id == project.id,
                TechnoCommercialTender.form_code.in_(["FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33", "FORM_STE", "FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_30_STE"])
            ).order_by(TechnoCommercialTender.id.desc()).first()
            if ste:
                if getattr(ste, "bid_submission_due_date_time", None):
                    return _format_date_val(ste.bid_submission_due_date_time), "Due Date"
                if getattr(ste, "tender_issue_date", None):
                    return _format_date_val(ste.tender_issue_date), "Tender Date"

        elif form_code_upper in ("FORM_34_BID_DOC_STE", "FORM_34_BID_DOCUMENT_STE"):
            from app.models.bid_document_ste import BidDocumentSte
            bd_ste = BidDocumentSte.query.filter_by(project_id=project.id).order_by(BidDocumentSte.id.desc()).first()
            if bd_ste:
                if getattr(bd_ste, "bid_submission_date", None):
                    return _format_date_val(bd_ste.bid_submission_date), "Submission Date"
                if getattr(bd_ste, "tender_issue_date", None):
                    return _format_date_val(bd_ste.tender_issue_date), "Tender Date"

        elif form_code_upper in ("FORM_35_ICB", "FORM_35_INTERNATIONAL_COMPETITIVE_BIDDING"):
            from app.models.international_competitive_bidding import InternationalCompetitiveBidding
            icb = InternationalCompetitiveBidding.query.filter_by(project_id=project.id).order_by(InternationalCompetitiveBidding.id.desc()).first()
            if icb:
                if getattr(icb, "bid_submission_due_date_time", None):
                    return _format_date_val(icb.bid_submission_due_date_time), "Due Date"
                if getattr(icb, "tender_issue_date", None):
                    return _format_date_val(icb.tender_issue_date), "Tender Date"

        elif form_code_upper in ("FORM_36_BID_DOC_ICB", "FORM_36_BID_DOCUMENT_ICB"):
            from app.models.bid_document_icb import BidDocumentIcb
            bd_icb = BidDocumentIcb.query.filter_by(project_id=project.id).order_by(BidDocumentIcb.id.desc()).first()
            if bd_icb:
                if getattr(bd_icb, "bid_submission_date", None):
                    return _format_date_val(bd_icb.bid_submission_date), "Submission Date"
                if getattr(bd_icb, "tender_issue_date", None):
                    return _format_date_val(bd_icb.tender_issue_date), "Tender Date"

        elif form_code_upper == "FORM_31_BID_DOC_LTE":
            bdl = BidDocumentLte.query.filter_by(project_id=project.id).order_by(BidDocumentLte.id.desc()).first()
            if bdl:
                if getattr(bdl, "bid_submission_date", None):
                    return _format_date_val(bdl.bid_submission_date), "Submission Date"

        elif form_code_upper == "FORM_32_EWAY_BILL":
            ewb = EWayBill.query.filter_by(project_id=project.id).order_by(EWayBill.id.desc()).first()
            if ewb:
                if getattr(ewb, "eway_bill_date", None):
                    return _format_date_val(ewb.eway_bill_date), "E-Way Date"

        elif form_code_upper == "FORM_21_TRANSPORTATION_DETAILS":
            td = TransportDetail.query.filter_by(project_id=project.id).order_by(TransportDetail.id.desc()).first()
            if td:
                if getattr(td, "dispatch_date", None):
                    return _format_date_val(td.dispatch_date), "Dispatch Date"
                if getattr(td, "delivery_date", None):
                    return _format_date_val(td.delivery_date), "Delivery Date"
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Error fetching step record date for project %s: %s", project.id, exc)

    # 3. Fallback: inspect any key in step.data that looks like a business date (never created/updated/completed)
    for k, v in step_data.items():
        k_lower = str(k).lower()
        if any(ign in k_lower for ign in ("created", "updated", "completed", "_auto", "_synced")):
            continue
        if "date" in k_lower or "deadline" in k_lower or "due" in k_lower or "time" in k_lower:
            formatted = _format_date_val(v)
            if formatted:
                label = LABEL_BY_KEY.get(k_lower, "Step Date")
                return formatted, label

    return None, None


def _get_project_fallback_item_date(project):
    """
    Checks all direct relational tables for any business date attached to this project.
    """
    try:
        # 1. Purchase Orders
        pos = getattr(project, "purchase_orders", None)
        if pos:
            for p in reversed(pos):
                if getattr(p, "po_date", None):
                    return _format_date_val(p.po_date), "PO Date"
                if getattr(p, "delivery_date", None):
                    return _format_date_val(p.delivery_date), "Delivery Date"

        # 2. Customer Quotations
        cqs = getattr(project, "customer_quotations", None)
        if cqs:
            for q in reversed(cqs):
                if getattr(q, "quotation_date", None):
                    return _format_date_val(q.quotation_date), "Quotation Date"

        # 3. Supplier Quotations
        sqs = getattr(project, "supplier_quotations", None)
        if sqs:
            for q in reversed(sqs):
                if getattr(q, "quotation_date", None):
                    return _format_date_val(q.quotation_date), "Quotation Date"

        # 4. Pre-Qualification Bids
        pqbs = getattr(project, "pre_qualification_bids", None)
        if pqbs:
            for b in reversed(pqbs):
                if getattr(b, "pqb_closing_date_time", None):
                    return _format_date_val(b.pqb_closing_date_time), "PQB Closed"
                if getattr(b, "pqb_issuing_date", None):
                    return _format_date_val(b.pqb_issuing_date), "PQB Issue Date"

        # 5. Customer Tenders
        cts = getattr(project, "customer_tenders", None)
        if cts:
            for t in reversed(cts):
                if getattr(t, "closing_date_time", None):
                    return _format_date_val(t.closing_date_time), "Closing Date"
                if getattr(t, "tender_date", None):
                    return _format_date_val(t.tender_date), "Tender Date"

        # 6. Customer Queries
        cqrys = getattr(project, "customer_queries", None)
        if cqrys:
            for q in reversed(cqrys):
                if getattr(q, "qo_date", None):
                    return _format_date_val(q.qo_date), "Query Date"

        # 7. Quotation Requests (RFQ)
        rfqs = getattr(project, "quotation_requests", None)
        if rfqs:
            for r in reversed(rfqs):
                if getattr(r, "quotation_requested_date", None):
                    return _format_date_val(r.quotation_requested_date), "RFQ Date"

        # 8. Bid Submissions
        bss = getattr(project, "bid_submissions", None)
        if bss:
            for b in reversed(bss):
                if getattr(b, "submission_date", None):
                    return _format_date_val(b.submission_date), "Submission Date"

        # 9. Invoices
        cdis = getattr(project, "customer_delivery_invoices", None)
        if cdis:
            for inv in reversed(cdis):
                if getattr(inv, "invoice_date", None):
                    return _format_date_val(inv.invoice_date), "Invoice Date"
                if getattr(inv, "due_date", None):
                    return _format_date_val(inv.due_date), "Due Date"

        sis = getattr(project, "supplier_invoices", None)
        if sis:
            for inv in reversed(sis):
                if getattr(inv, "invoice_date", None):
                    return _format_date_val(inv.invoice_date), "Invoice Date"
                if getattr(inv, "due_date", None):
                    return _format_date_val(inv.due_date), "Due Date"

        # 10. Challans
        dcs = getattr(project, "delivery_challans", None)
        if dcs:
            for dc in reversed(dcs):
                if getattr(dc, "delivery_challan_date", None):
                    return _format_date_val(dc.delivery_challan_date), "Challan Date"

        # 11. Payments
        cps = getattr(project, "customer_payments", None)
        if cps:
            for cp in reversed(cps):
                if getattr(cp, "payment_date", None):
                    return _format_date_val(cp.payment_date), "Payment Date"

        sps = getattr(project, "supplier_payments", None)
        if sps:
            for sp in reversed(sps):
                if getattr(sp, "payment_date", None):
                    return _format_date_val(sp.payment_date), "Payment Date"
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Failed _get_project_fallback_item_date for project %s: %s", getattr(project, "id", None), exc)

    return None, None


def _project_response(project):
    total_margin, margin_percentage = _get_project_margin_info(project.id)
    steps = project.steps if hasattr(project, "steps") and project.steps else []
    saved_steps = [s for s in steps if getattr(s, "id", None) is not None]
    current_step_date = None
    current_step_date_label = None
    if saved_steps:
        in_progress_steps = [s for s in saved_steps if s.status == "in_progress"]
        active_or_completed_steps = [
            s for s in saved_steps if s.status in ("in_progress", "completed")
        ]
        curr_s = in_progress_steps[0] if in_progress_steps else (active_or_completed_steps[-1] if active_or_completed_steps else saved_steps[-1])
        current_step_date, current_step_date_label = _get_step_item_date(project, curr_s)
        if not current_step_date and active_or_completed_steps:
            for prev_s in reversed(active_or_completed_steps):
                if prev_s != curr_s:
                    prev_date, prev_label = _get_step_item_date(project, prev_s)
                    if prev_date:
                        current_step_date = prev_date
                        current_step_date_label = prev_label
                        break
        if not current_step_date and saved_steps:
            for prev_s in reversed(saved_steps):
                if prev_s != curr_s:
                    prev_date, prev_label = _get_step_item_date(project, prev_s)
                    if prev_date:
                        current_step_date = prev_date
                        current_step_date_label = prev_label
                        break
    if not current_step_date:
        current_step_date, current_step_date_label = _get_project_fallback_item_date(project)

    return {
        "id": project.id,
        "project_code": project.project_code,
        "project_title": project.project_title,
        "nickname": project.nickname,
        "customer_id": project.customer_id,
        "supplier_id": project.supplier_id,
        "current_step_date": current_step_date,
        "current_step_date_label": current_step_date_label,
        "step_date": current_step_date,
        "step_date_label": current_step_date_label,
        "total_margin": total_margin,
        "margin_percentage": margin_percentage,
        "margin_percent": margin_percentage,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


def _project_summary_response(project):
    try:
        from app.routes.project_step import sync_project_steps_from_records
        sync_project_steps_from_records(project)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("sync_project_steps_from_records failed for project %s: %s", getattr(project, "id", None), exc)
    steps = project.steps if hasattr(project, "steps") and project.steps else []

    saved_steps = [s for s in steps if getattr(s, "id", None) is not None]
    curr_s = None
    if saved_steps:
        total_steps = len(saved_steps)
        completed_steps_count = len([s for s in saved_steps if s.status == "completed"])
        progress_percentage = round((completed_steps_count / total_steps) * 100) if total_steps > 0 else 0

        in_progress_steps = [s for s in saved_steps if s.status == "in_progress"]
        active_or_completed_steps = [
            s for s in saved_steps if s.status in ("in_progress", "completed")
        ]
        if in_progress_steps:
            curr_s = in_progress_steps[0]
        elif active_or_completed_steps:
            curr_s = active_or_completed_steps[-1]
        else:
            curr_s = saved_steps[-1]

        current_step_number = curr_s.step_order or curr_s.step_number or 1
        current_step_name = curr_s.step_name or STEP_NAMES.get(current_step_number) or f"Step {current_step_number}"
        current_form_code = getattr(curr_s, "form_code", None)
    else:
        total_steps = 0
        completed_steps_count = 0
        progress_percentage = 0
        current_step_number = 0
        current_step_name = "No steps attached"
        current_form_code = None
        in_progress_steps = []
        active_or_completed_steps = []

    current_step_date = None
    current_step_date_label = None
    if curr_s:
        current_step_date, current_step_date_label = _get_step_item_date(project, curr_s)
    if not current_step_date and active_or_completed_steps:
        for prev_s in reversed(active_or_completed_steps):
            if prev_s != curr_s:
                prev_date, prev_label = _get_step_item_date(project, prev_s)
                if prev_date:
                    current_step_date = prev_date
                    current_step_date_label = prev_label
                    break
    if not current_step_date and saved_steps:
        for prev_s in reversed(saved_steps):
            if prev_s != curr_s:
                prev_date, prev_label = _get_step_item_date(project, prev_s)
                if prev_date:
                    current_step_date = prev_date
                    current_step_date_label = prev_label
                    break
    if not current_step_date:
        current_step_date, current_step_date_label = _get_project_fallback_item_date(project)

    # Project overall status in dynamic workflow:
    # Only mark completed if all attached steps are completed AND a terminal settlement/delivery step is completed
    terminal_form_codes = {
        "FORM_20_PAYMENT_TO_SUPPLIER",
        "FORM_22_PAYMENT_FROM_CUSTOMER",
        "FORM_23_WARRANTY_CERTIFICATE",
        "FORM_24_DELIVERY_CHALLAN",
        "FORM_26_TAX_INVOICE_CUSTOMER",
    }
    has_terminal_step = any(
        getattr(s, "form_code", None) in terminal_form_codes and s.status == "completed"
        for s in saved_steps
    )

    if total_steps > 0 and completed_steps_count == total_steps and has_terminal_step:
        status = "completed"
    elif active_or_completed_steps:
        status = "in_progress"
    else:
        status = "pending"

    next_action = None
    # Target delivery date resolution
    target_delivery_date = None
    po = None
    try:
        po = (
            PurchaseOrder.query.filter_by(project_id=project.id)
            .order_by(PurchaseOrder.id.desc())
            .first()
        )
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Failed to fetch po for project %s: %s", project.id, exc)

    if po and po.delivery_date:
        target_delivery_date = (
            po.delivery_date.isoformat()
            if hasattr(po.delivery_date, "isoformat")
            else str(po.delivery_date)[:10]
        )

    if not target_delivery_date:
        try:
            order_conf = (
                SupplierOrderConfirmation.query.filter_by(project_id=project.id)
                .order_by(SupplierOrderConfirmation.id.desc())
                .first()
            )
            if order_conf and order_conf.expected_delivery_date:
                target_delivery_date = (
                    order_conf.expected_delivery_date.isoformat()
                    if hasattr(order_conf.expected_delivery_date, "isoformat")
                    else str(order_conf.expected_delivery_date)[:10]
                )
        except Exception as exc:
            db.session.rollback()
            current_app.logger.warning("Failed to fetch order_conf for project %s: %s", project.id, exc)

    if not target_delivery_date:
        for s in reversed(steps):
            if s.data and isinstance(s.data, dict):
                d = (
                    s.data.get("delivery_date")
                    or s.data.get("expected_delivery_date")
                    or s.data.get("target_delivery_date")
                )
                if d:
                    target_delivery_date = str(d)[:10]
                    break

    if not current_step_date and target_delivery_date:
        current_step_date = target_delivery_date
        current_step_date_label = "Delivery Date"

    # Total value and currency resolution
    total_value = None
    currency = "INR"

    # Priority 1: Customer's Purchase Order
    if po:
        if po.total_gross_amount is not None:
            total_value = float(po.total_gross_amount)
        elif po.total_net_amount is not None:
            total_value = float(po.total_net_amount)

    # Priority 2: Tender Document (Bid Submission)
    if total_value is None:
        try:
            bid = (
                BidSubmission.query.filter_by(project_id=project.id)
                .order_by(BidSubmission.id.desc())
                .first()
            )
            if bid and bid.items:
                net_sum = 0.0
                for item in bid.items:
                    if item.net_total is not None:
                        net_sum += float(item.net_total)
                    elif item.unit_price is not None and item.quantity is not None:
                        net_sum += float(item.unit_price) * float(item.quantity)
                if net_sum > 0:
                    if bid.gst_rate is not None:
                        try:
                            total_value = round(net_sum * (1.0 + float(bid.gst_rate) / 100.0), 2)
                        except Exception:
                            total_value = net_sum
                    else:
                        total_value = net_sum
        except Exception as exc:
            db.session.rollback()
            current_app.logger.warning("Failed to fetch bid for project %s: %s", project.id, exc)

    # Priority 3: Quotation submitted to the customer
    if total_value is None:
        try:
            cq = (
                CustomerQuotation.query.filter_by(project_id=project.id)
                .order_by(CustomerQuotation.id.desc())
                .first()
            )
            if cq:
                if cq.total_net_amount is not None:
                    total_value = float(cq.total_net_amount)
                elif cq.quotation_value is not None:
                    total_value = float(cq.quotation_value)
                if cq.currency_unit:
                    currency = cq.currency_unit
        except Exception as exc:
            db.session.rollback()
            current_app.logger.warning("Failed to fetch cq for project %s: %s", project.id, exc)

    # Priority 4: Default value - 0
    if total_value is not None:
        if total_value == int(total_value):
            total_value = int(total_value)
        else:
            total_value = round(total_value, 2)
    else:
        total_value = 0

    # Total margin and margin percentage resolution from Cost Sheet
    total_margin, margin_percentage = _get_project_margin_info(project.id)

    # Payment statuses
    customer_payment_status = "pending"
    cust_payments = []
    try:
        cust_payments = (
            CustomerPayment.query.filter_by(project_id=project.id)
            .order_by(CustomerPayment.created_at.asc(), CustomerPayment.id.asc())
            .all()
        )
        if cust_payments:
            paid_sum = sum(
                float(p.payment_amount or 0) + float(p.tds or 0) + float(p.ld or 0)
                for p in cust_payments
            )
            latest_cust = cust_payments[-1]
            cust_iv = (
                float(latest_cust.invoice_value)
                if latest_cust.invoice_value is not None and float(latest_cust.invoice_value) > 0
                else float(total_value or 0.0)
            )
            latest_pending = max(cust_iv - paid_sum, 0.0) if cust_iv > 0 else 0.0
            if (cust_iv > 0 and paid_sum >= cust_iv) or (latest_pending <= 0 and paid_sum > 0):
                customer_payment_status = "completed"
            elif paid_sum > 0:
                customer_payment_status = "partial"
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Failed to fetch cust_payments for project %s: %s", project.id, exc)
        cust_payments = []

    if not cust_payments:
        s14 = next((s for s in steps if s.step_number == 14), None)
        if s14:
            if s14.status == "completed":
                customer_payment_status = "completed"
            elif s14.status == "in_progress":
                customer_payment_status = "partial"

    supplier_payment_status = "pending"
    supp_payments = []
    try:
        supp_payments = (
            SupplierPayment.query.filter_by(project_id=project.id)
            .order_by(SupplierPayment.created_at.asc(), SupplierPayment.id.asc())
            .all()
        )
        if supp_payments:
            paid_sum = sum(float(p.amount_paid) for p in supp_payments if p.amount_paid is not None)
            latest_supp = supp_payments[-1]
            supp_tsv = (
                float(latest_supp.total_supplier_value)
                if latest_supp.total_supplier_value is not None
                else 0.0
            )
            latest_pending = (
                float(latest_supp.pending_amount)
                if latest_supp.pending_amount is not None
                else max(supp_tsv - paid_sum, 0.0)
            )
            if (supp_tsv > 0 and paid_sum >= supp_tsv) or (latest_pending <= 0 and paid_sum > 0):
                supplier_payment_status = "completed"
            elif paid_sum > 0:
                supplier_payment_status = "partial"
    except Exception as exc:
        db.session.rollback()
        current_app.logger.warning("Failed to fetch supp_payments for project %s: %s", project.id, exc)
        supp_payments = []

    if not supp_payments:
        s15 = next((s for s in steps if s.step_number == 15), None)
        if s15:
            if s15.status == "completed":
                supplier_payment_status = "completed"
            elif s15.status == "in_progress":
                supplier_payment_status = "partial"

    return {
        "id": project.id,
        "project_code": project.project_code,
        "project_title": project.project_title,
        "nickname": project.nickname,
        "customer_id": project.customer_id,
        "customer_name": project.customer.name if project.customer else "",
        "supplier_id": project.supplier_id,
        "supplier_name": project.supplier.name if project.supplier else "",
        "current_step_number": current_step_number,
        "total_steps": total_steps,
        "completed_steps_count": completed_steps_count,
        "current_step_name": current_step_name,
        "current_form_code": current_form_code,
        "current_step_date": current_step_date,
        "current_step_date_label": current_step_date_label,
        "step_date": current_step_date,
        "step_date_label": current_step_date_label,
        "progress_percentage": progress_percentage,
        "status": status,
        "next_action": next_action,
        "target_delivery_date": target_delivery_date,
        "total_value": total_value,
        "total_margin": total_margin,
        "margin_percentage": margin_percentage,
        "margin_percent": margin_percentage,
        "currency": currency,
        "customer_payment_status": customer_payment_status,
        "supplier_payment_status": supplier_payment_status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


@project_bp.post("")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.arguments(ProjectCreateSchema)
@project_bp.response(201, ProjectResponseSchema)
@jwt_required()
def create(data):
    try:
        project = create_project(
            project_title=data["project_title"],
            customer_id=data["customer_id"],
            supplier_id=data["supplier_id"],
            project_code=data.get("project_code"),
            nickname=data.get("nickname"),
        )

    except CustomerNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except SupplierNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _project_response(project), 201


@project_bp.get("")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.response(200, ProjectListResponseSchema)
@jwt_required()
def list_all():
    projects = list_projects()

    return {
        "success": True,
        "message": "Projects fetched successfully",
        "data": [
            _project_summary_response(project)
            for project in projects
        ],
    }, 200


@project_bp.get("/search")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.arguments(ProjectSearchQuerySchema, location="query")
@project_bp.response(200, ProjectSearchResponseSchema)
@jwt_required()
def search(args):
    query_str = (args.get("q") or "").strip().lower() if args else ""
    projects = list_projects()

    matched_projects = []
    for project in projects:
        step_num, step_name, latest_items = _get_project_latest_items(project.id)

        if not query_str:
            summary = _project_summary_response(project)
            summary["matched_items"] = []
            matched_projects.append(summary)
            continue

        title_match = bool(project.project_title and query_str in project.project_title.lower())
        code_match = bool(project.project_code and query_str in project.project_code.lower())

        item_matches = [
            it
            for it in latest_items
            if it.get("material_name") and query_str in it["material_name"].lower()
        ]

        if title_match or code_match or item_matches:
            summary = _project_summary_response(project)
            summary["matched_items"] = item_matches
            matched_projects.append(summary)

    return {
        "success": True,
        "message": "Projects searched successfully",
        "data": matched_projects,
    }, 200


@project_bp.get("/<int:project_id>")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.response(200, ProjectResponseSchema)
@jwt_required()
def get(project_id):
    try:
        project = get_project(project_id)

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _project_response(project), 200


@project_bp.put("/<int:project_id>")
@project_bp.patch("/<int:project_id>")
@project_bp.doc(security=[{"BearerAuth": []}])
@project_bp.arguments(ProjectUpdateSchema)
@project_bp.response(200, ProjectResponseSchema)
@jwt_required()
def update(data, project_id):
    try:
        project = update_project(
            project_id,
            project_title=data.get("project_title"),
            customer_id=data.get("customer_id"),
            supplier_id=data.get("supplier_id"),
            project_code=data.get("project_code"),
            nickname=data.get("nickname"),
        )

    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except CustomerNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    except SupplierNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "SUPPLIER_NOT_FOUND",
                "message": str(exc),
            },
        }, 404

    return _project_response(project), 200


@project_bp.delete("/<int:project_id>")
@project_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def delete(project_id):
    try:
        delete_project(project_id)
        return jsonify({
            "success": True,
            "message": f"Project {project_id} and all associated data deleted successfully.",
            "data": {
                "id": project_id,
            },
        }), 200
    except ProjectNotFoundError as exc:
        return {
            "success": False,
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
            },
        }, 404
    except Exception:
        current_app.logger.exception("Failed to delete project")
        return {
            "success": False,
            "error": {
                "code": "PROJECT_DELETE_FAILED",
                "message": "Failed to delete project.",
            },
        }, 500
