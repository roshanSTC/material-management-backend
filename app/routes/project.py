from flask import current_app, jsonify
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.models import (
    BidSubmission,
    CostSheet,
    CustomerDeliveryInvoice,
    CustomerDeliveryPackingList,
    CustomerPayment,
    CustomerQuery,
    CustomerQuotation,
    CustomerTender,
    DeliveryChallan,
    PurchaseOrder,
    QuotationRequest,
    SupplierInvoice,
    SupplierOrderConfirmation,
    SupplierPackingList,
    SupplierPayment,
    SupplierProformaInvoice,
    SupplierQuotation,
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
    except Exception:
        pass
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
        pass

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
        pass

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
        pass

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
        pass

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
        pass

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
        pass

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
        pass

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
        pass

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
        pass

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
        pass

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
        pass

    return None, None, []


def _project_response(project):
    total_margin, margin_percentage = _get_project_margin_info(project.id)
    return {
        "id": project.id,
        "project_code": project.project_code,
        "project_title": project.project_title,
        "nickname": project.nickname,
        "customer_id": project.customer_id,
        "supplier_id": project.supplier_id,
        "total_margin": total_margin,
        "margin_percentage": margin_percentage,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


def _project_summary_response(project):
    steps = project.steps if hasattr(project, "steps") and project.steps else []

    # Current step number
    in_progress_steps = [s for s in steps if s.status == "in_progress"]
    active_or_completed_steps = [
        s for s in steps if s.status in ("in_progress", "completed")
    ]
    if in_progress_steps:
        current_step_number = min(s.step_number for s in in_progress_steps)
    elif active_or_completed_steps:
        current_step_number = max(s.step_number for s in active_or_completed_steps)
    elif steps:
        current_step_number = max(s.step_number for s in steps)
    else:
        current_step_number = 1

    total_steps = 15
    current_step_number = max(1, min(total_steps, current_step_number))
    current_step_name = STEP_NAMES.get(current_step_number, f"Step {current_step_number}")

    completed_step_numbers = {
        s.step_number
        for s in steps
        if s.status == "completed" and 1 <= s.step_number <= total_steps
    }
    completed_steps_count = len(completed_step_numbers)
    progress_percentage = round((completed_steps_count / total_steps) * 100)

    # Project overall status
    if completed_steps_count == total_steps:
        status = "completed"
    elif active_or_completed_steps:
        status = "in_progress"
    else:
        status = "pending"

    next_action = STEP_NEXT_ACTIONS.get(current_step_number, "Review project status")

    # Target delivery date resolution
    target_delivery_date = None
    po = None
    try:
        po = (
            PurchaseOrder.query.filter_by(project_id=project.id)
            .order_by(PurchaseOrder.id.desc())
            .first()
        )
    except Exception:
        pass

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
        except Exception:
            pass

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
        except Exception:
            pass

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
        except Exception:
            pass

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
    except Exception:
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
    except Exception:
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
        "current_step_name": current_step_name,
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

