from datetime import date, datetime

from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint

from app.models import (
    CostSheet,
    CustomerPayment,
    CustomerQuotation,
    PurchaseOrder,
    SupplierInvoice,
    SupplierOrderConfirmation,
    SupplierPayment,
)
from app.schemas.project import (
    ProjectCreateSchema,
    ProjectListResponseSchema,
    ProjectResponseSchema,
    ProjectUpdateSchema,
)
from app.services.project_service import (
    CustomerNotFoundError,
    ProjectNotFoundError,
    SupplierNotFoundError,
    create_project,
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
    1: "Customer Query to ST",
    2: "Request Quotation from Supplier",
    3: "Supplier's Quotation",
    4: "Cost Sheet Preparation",
    5: "Quotation to Customer",
    6: "Customer issues Tender",
    7: "S.T. submits Bid Documents",
    8: "Customer issues Purchase Order (PO)",
    9: "S.T. places Order Confirmation with Supplier",
    10: "Supplier raises Bill / Invoice",
    11: "Material delivered to India",
    12: "Customs Clearance",
    13: "Customer Delivery with S.T. Billing",
    14: "Customer makes Payment to S.T.",
    15: "S.T. makes Payment to Partner / Supplier",
}

STEP_NEXT_ACTIONS = {
    1: "Review Customer Query & Requirements",
    2: "Request Quotation from Overseas Supplier",
    3: "Evaluate Supplier Quotation & Terms",
    4: "Prepare Landed Cost Sheet",
    5: "Send Formal Quotation to Customer",
    6: "Review Customer Tender Requirements",
    7: "Prepare & Submit Bid Documents",
    8: "Verify Customer PO document",
    9: "Place Order Confirmation with Supplier",
    10: "Verify Supplier Commercial Invoice",
    11: "Track Material Shipment to India",
    12: "Complete Customs Clearance Formalities",
    13: "Confirm Material Delivery Receipt",
    14: "Follow up for Customer Payment",
    15: "Settle Balance Payment to Supplier",
}


def _project_response(project):
    return {
        "id": project.id,
        "project_title": project.project_title,
        "customer_id": project.customer_id,
        "supplier_id": project.supplier_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }


def _project_summary_response(project):
    steps = project.steps if hasattr(project, "steps") and project.steps else []

    # Current step number
    in_progress_steps = [s for s in steps if s.status == "in_progress"]
    if in_progress_steps:
        current_step_number = min(s.step_number for s in in_progress_steps)
    elif steps:
        current_step_number = max(s.step_number for s in steps)
    else:
        current_step_number = 1

    current_step_number = max(1, min(15, current_step_number))
    total_steps = 15
    current_step_name = STEP_NAMES.get(current_step_number, f"Step {current_step_number}")
    progress_percentage = round((current_step_number / 15) * 100) if (steps or current_step_number > 1) else 0

    # Project overall status
    if current_step_number == 15 and any(s.step_number == 15 and s.status == "completed" for s in steps):
        status = "completed"
    elif steps:
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

    # Health status based on target delivery date
    health_status = "on_track"
    if status == "completed":
        health_status = "completed"
    elif target_delivery_date:
        try:
            del_d = date.fromisoformat(str(target_delivery_date)[:10])
            today = date.today()
            diff = (del_d - today).days
            if diff < 0:
                health_status = "delayed"
            elif diff <= 7:
                health_status = "at_risk"
            else:
                health_status = "on_track"
        except Exception:
            health_status = "on_track"

    # Total value and currency resolution
    total_value = None
    currency = "INR"

    if po:
        if po.total_gross_amount is not None:
            total_value = float(po.total_gross_amount)
        elif po.total_net_amount is not None:
            total_value = float(po.total_net_amount)

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

    if total_value is None:
        try:
            cs = (
                CostSheet.query.filter_by(project_id=project.id)
                .order_by(CostSheet.version_number.desc())
                .first()
            )
            if cs and cs.output and isinstance(cs.output, dict):
                fp = cs.output.get("final_price") or cs.output.get("total_amount")
                if fp is not None:
                    try:
                        total_value = float(fp)
                    except (ValueError, TypeError):
                        pass
        except Exception:
            pass

    if total_value is None:
        try:
            inv = (
                SupplierInvoice.query.filter_by(project_id=project.id)
                .order_by(SupplierInvoice.id.desc())
                .first()
            )
            if inv:
                if inv.total_amount is not None:
                    total_value = float(inv.total_amount)
                elif inv.total_net_amount is not None:
                    total_value = float(inv.total_net_amount)
        except Exception:
            pass

    if total_value is None:
        for s in reversed(steps):
            if s.data and isinstance(s.data, dict):
                val = (
                    s.data.get("po_amount")
                    or s.data.get("quotation_amount")
                    or s.data.get("total_gross_amount")
                    or s.data.get("invoice_amount")
                )
                if val is not None:
                    try:
                        total_value = float(val)
                        break
                    except (ValueError, TypeError):
                        pass

    if total_value is not None:
        if total_value == int(total_value):
            total_value = int(total_value)
        else:
            total_value = round(total_value, 2)
    else:
        total_value = 0

    # Payment statuses
    customer_payment_status = "pending"
    cust_payments = []
    try:
        cust_payments = CustomerPayment.query.filter_by(project_id=project.id).all()
        if cust_payments:
            paid_sum = sum(float(p.payment_amount) for p in cust_payments if p.payment_amount is not None)
            if total_value and paid_sum >= total_value:
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
        supp_payments = SupplierPayment.query.filter_by(project_id=project.id).all()
        if supp_payments:
            paid_sum = sum(float(p.amount_paid_inr) for p in supp_payments if p.amount_paid_inr is not None)
            has_pending = any(p.pending_amount and float(p.pending_amount) > 0 for p in supp_payments)
            if not has_pending and paid_sum > 0:
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
        "project_title": project.project_title,
        "customer_id": project.customer_id,
        "customer_name": project.customer.name if project.customer else "",
        "supplier_id": project.supplier_id,
        "supplier_name": project.supplier.name if project.supplier else "",
        "current_step_number": current_step_number,
        "total_steps": total_steps,
        "current_step_name": current_step_name,
        "progress_percentage": progress_percentage,
        "status": status,
        "health_status": health_status,
        "next_action": next_action,
        "target_delivery_date": target_delivery_date,
        "total_value": total_value,
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
