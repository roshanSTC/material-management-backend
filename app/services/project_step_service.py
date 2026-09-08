from datetime import datetime, timezone

from app.extensions.database import db
from app.models import (
    BidSubmission,
    CustomerTender,
    Project,
    ProjectStep,
    PurchaseOrder,
    SupplierOrderConfirmation,
)

STEP_DEFINITIONS = {
    1: {
        "name": "Customer Query to ST",
        "description": (
            "Customer shares the material or equipment requirement "
            "with S.T."
        ),
        "required_fields": {
            "qo_date",
            "remark",  
        },
    },
    2: {
        "name": "Request Quotation from Supplier",
        "description": (
            "S.T. forwards the requirement to the overseas partner "
            "or supplier for pricing."
        ),
        "required_fields": {
            "quotation_requested_date",
            "supplier_contacted",
            "remarks",
        },
    },
    3: {
        "name": "Supplier's Quotation",
        "description": (
            "The supplier returns pricing, lead time, and terms "
            "for the requested material."
        ),
        "required_fields": {
            "quotation_number",
            "quotation_value",
            "quotation_date",
            "currency_unit",
            "validity",
            "incoterms",
            "payment_terms",
            "delivery_period",
            "remark",
        },
    },
    4: {
        "name": "Cost Sheet Preparation",
        "description": (
            "Landed cost, duties, margin, and freight are worked "
            "into an internal cost sheet."
        ),
        "required_fields": {
            "cost_amount",
            "margin_percent",
            "prepared_date",
            "remarks",
        },
    },
    5: {
        "name": "Quotation to Customer",
        "description": (
            "A formal quotation is issued to the customer based "
            "on the cost sheet."
        ),
        "required_fields": {
            "quotation_amount",
            "sent_date",
            "validity_days",
            "remarks",
        },
    },
    6: {
        "name": "Customer issues Tender",
        "description": (
            "The customer floats a tender based on the quoted scope."
        ),
        "required_fields": {
            "tender_number",
            "submission_date",
            "remarks",
        },
    },
    7: {
        "name": "S.T. submits Bid Documents",
        "description": (
            "S.T. prepares and submits the technical and commercial bid."
        ),
        "required_fields": {
            "document_reference",
            "submitted_date",
            "remarks",
        },
    },
    8: {
        "name": "Customer issues Purchase Order (PO)",
        "description": (
            "On winning the bid, the customer issues an official "
            "PO to S.T."
        ),
        "required_fields": {
            "po_number",
            "po_date",
            "po_amount",
            "remarks",
        },
    },
    9: {
        "name": (
            "S.T. places Order Confirmation with Supplier"
        ),
        "description": (
            "S.T. confirms the order with the foreign partner "
            "or supplier."
        ),
        "required_fields": {
            "confirmation_date",
            "expected_delivery_date",
            "remarks",
        },
    },
    10: {
        "name": "Supplier raises Bill / Invoice",
        "description": (
            "The supplier issues billing, triggering the advance "
            "payment terms."
        ),
        "required_fields": {
            "invoice_number",
            "invoice_date",
            "invoice_amount",
            "remarks",
        },
    },
    11: {
        "name": "Material delivered to India",
        "description": (
            "Goods arrive at the Indian port or airport for clearance."
        ),
        "required_fields": {
            "shipping_mode",
            "tracking_number",
            "dispatch_date",
            "remarks",
        },
    },
    12: {
        "name": "Customs Clearance",
        "description": (
            "Import documentation, duties, and customs formalities "
            "are completed."
        ),
        "required_fields": {
            "clearance_date",
            "duties_paid",
            "agent_name",
            "remarks",
        },
    },
    13: {
        "name": (
            "S.T. delivers Material to Customer's Place "
            "with S.T. Billing"
        ),
        "description": (
            "Material reaches the customer's site along with "
            "S.T.'s invoice."
        ),
        "required_fields": {
            "delivery_date",
            "delivery_challan_number",
            "remarks",
        },
    },
    14: {
        "name": "Customer makes Payment to S.T.",
        "description": (
            "Customer settles the invoice raised by S.T."
        ),
        "required_fields": {
            "payment_date",
            "amount_received",
            "payment_mode",
            "remarks",
        },
    },
    15: {
        "name": "S.T. makes Payment to Partner / Supplier",
        "description": (
            "S.T. clears the balance payment owed to the supplier."
        ),
        "required_fields": {
            "payment_date",
            "amount_paid",
            "payment_mode",
            "remarks",
        },
    },
}


VALID_STATUSES = {
    "pending",
    "in_progress",
    "completed",
}


class ProjectStepError(Exception):
    """Base exception for project step operations."""


class ProjectNotFoundError(ProjectStepError):
    pass


class ProjectStepNotFoundError(ProjectStepError):
    pass


class ProjectStepAlreadyExistsError(ProjectStepError):
    pass


class InvalidStepNumberError(ProjectStepError):
    pass


class InvalidStepStatusError(ProjectStepError):
    pass


class InvalidStepDataError(ProjectStepError):
    pass


def _get_step_definition(step_number: int) -> dict:
    definition = STEP_DEFINITIONS.get(step_number)

    if definition is None:
        raise InvalidStepNumberError(
            "Step number must be between 1 and 15."
        )

    return definition


def _is_field_filled(value) -> bool:
    """
    Determine whether a required field has been provided.

    None and empty strings are considered empty.

    Values such as 0 and False are considered valid values.
    """
    if value is None:
        return False

    if isinstance(value, str) and not value.strip():
        return False

    return True


def calculate_step_progress(
    step_number: int,
    data: dict | None,
) -> float:
    """
    Calculate the completion percentage for a project step.
    """
    definition = _get_step_definition(step_number)

    required_fields = definition["required_fields"]

    if not required_fields:
        return 100.0

    data = data or {}

    filled_fields = sum(
        1
        for field_name in required_fields
        if _is_field_filled(data.get(field_name))
    )

    percentage = (
        filled_fields / len(required_fields)
    ) * 100

    return round(percentage, 2)


def determine_step_status(progress_percentage: float) -> str:
    """
    Determine step status from its completion percentage.
    """
    if progress_percentage <= 0:
        return "pending"

    if progress_percentage >= 100:
        return "completed"

    return "in_progress"


def _calculate_step_state(
    step_number: int,
    data: dict | None,
) -> tuple[str, float]:
    """
    Calculate both status and percentage for a step.
    """
    progress_percentage = calculate_step_progress(
        step_number,
        data,
    )

    status = determine_step_status(
        progress_percentage
    )

    return status, progress_percentage


def _validate_data(
    step_number: int,
    data: dict | None,
) -> dict | None:
    if data is None:
        return None

    if not isinstance(data, dict):
        raise InvalidStepDataError(
            "Step data must be a JSON object."
        )

    definition = _get_step_definition(step_number)

    allowed_fields = definition["required_fields"]

    unknown_fields = set(data) - allowed_fields

    if unknown_fields:
        raise InvalidStepDataError(
            f"Unsupported fields for step {step_number}: "
            f"{', '.join(sorted(unknown_fields))}"
        )

    return data


def list_project_steps(
    project_id: int,
) -> list[ProjectStep]:
    project = db.session.get(Project, project_id)

    if project is None:
        raise ProjectNotFoundError(
            f"Project with id {project_id} was not found."
        )

    saved_steps = {
        step.step_number: step
        for step in ProjectStep.query
        .filter_by(project_id=project_id)
        .order_by(ProjectStep.step_number)
        .all()
    }

    result = []

    for step_number, definition in STEP_DEFINITIONS.items():
        step = saved_steps.get(step_number)

        if step is None:
            step = ProjectStep(
                id=None,
                project_id=project_id,
                step_number=step_number,
                step_name=definition["name"],
                description=definition["description"],
                status="pending",
                completed_at=None,
                data=None,
            )

        result.append(step)

    return result


def get_project_step(
    project_id: int,
    step_number: int,
) -> ProjectStep:
    if db.session.get(Project, project_id) is None:
        raise ProjectNotFoundError(
            f"Project with id {project_id} was not found."
        )

    _get_step_definition(step_number)

    step = ProjectStep.query.filter_by(
        project_id=project_id,
        step_number=step_number,
    ).first()

    if step is None:
        raise ProjectStepNotFoundError(
            f"Step {step_number} has not been saved "
            f"for project {project_id}."
        )

    return step


def create_project_step(
    *,
    project_id: int,
    step_number: int,
    data: dict | None,
) -> ProjectStep:
    if db.session.get(Project, project_id) is None:
        raise ProjectNotFoundError(
            f"Project with id {project_id} was not found."
        )

    definition = _get_step_definition(step_number)

    data = _validate_data(
        step_number,
        data,
    )

    status, progress_percentage = _calculate_step_state(
        step_number,
        data,
    )

    existing = ProjectStep.query.filter_by(
        project_id=project_id,
        step_number=step_number,
    ).first()

    if existing is not None:
        raise ProjectStepAlreadyExistsError(
            f"Step {step_number} already exists "
            f"for project {project_id}."
        )

    step = ProjectStep(
        project_id=project_id,
        step_number=step_number,
        step_name=definition["name"],
        description=definition["description"],
        status=status,
        completed_at=(
            datetime.now(timezone.utc)
            if status == "completed"
            else None
        ),
        data=data,
    )

    db.session.add(step)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return step


def update_project_step(
    *,
    project_id: int,
    step_number: int,
    data: dict | None,
) -> ProjectStep:
    step = get_project_step(
        project_id=project_id,
        step_number=step_number,
    )

    data = _validate_data(
        step_number,
        data,
    )

    status, progress_percentage = _calculate_step_state(
        step_number,
        data,
    )

    step.status = status
    step.data = data

    step.completed_at = (
        datetime.now(timezone.utc)
        if status == "completed"
        else None
    )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return step


def get_all_project_steps(
    project_id: int,
) -> list[ProjectStep]:
    return list_project_steps(project_id)


def get_single_project_step(
    project_id: int,
    step_number: int,
) -> ProjectStep:
    return get_project_step(
        project_id=project_id,
        step_number=step_number,
    )


def create_project_step_transaction(
    *,
    project_id: int,
    step_number: int,
    data: dict | None,
) -> ProjectStep:
    return create_project_step(
        project_id=project_id,
        step_number=step_number,
        data=data,
    )


def update_project_step_transaction(
    *,
    project_id: int,
    step_number: int,
    data: dict | None,
) -> ProjectStep:
    return update_project_step(
        project_id=project_id,
        step_number=step_number,
        data=data,
    )


def serialize_project_step(step: ProjectStep) -> dict:
    status, progress_percentage = _calculate_step_state(
        step.step_number,
        step.data,
    )

    return {
        "id": step.id,
        "project_id": step.project_id,
        "step_number": step.step_number,
        "step_name": step.step_name,
        "description": step.description,
        "status": status,
        "progress_percentage": progress_percentage,
        "completed_at": step.completed_at,
        "data": step.data,
    }


def upsert_project_step_record(
    *,
    project_id: int,
    step_number: int,
    data: dict | None,
) -> ProjectStep:
    definition = _get_step_definition(step_number)

    status, progress_percentage = _calculate_step_state(
        step_number,
        data,
    )

    step = ProjectStep.query.filter_by(
        project_id=project_id,
        step_number=step_number,
    ).first()

    if step is None:
        step = ProjectStep(
            project_id=project_id,
            step_number=step_number,
            step_name=definition["name"],
            description=definition["description"],
            status=status,
            completed_at=(
                datetime.now(timezone.utc)
                if status == "completed"
                else None
            ),
            data=data,
        )
        db.session.add(step)
    else:
        step.status = status
        step.data = data
        step.completed_at = (
            datetime.now(timezone.utc)
            if status == "completed"
            else None
        )

    db.session.flush()
    return step


def sync_customer_query_step(project_id: int) -> ProjectStep | None:
    from app.models.customer_query import CustomerQuery

    project = db.session.get(Project, project_id)
    if project is None:
        return None

    customer_query = (
        CustomerQuery.query
        .filter_by(project_id=project_id)
        .order_by(CustomerQuery.updated_at.desc(), CustomerQuery.id.desc())
        .first()
    )

    if customer_query is None:
        existing_step = ProjectStep.query.filter_by(
            project_id=project_id,
            step_number=1,
        ).first()

        if existing_step is not None:
            db.session.delete(existing_step)
            db.session.flush()
        return None

    step_data = {
        "qo_date": (
            customer_query.qo_date.isoformat()
            if hasattr(customer_query.qo_date, "isoformat")
            else str(customer_query.qo_date)
        ) if customer_query.qo_date else None,
        "remark": customer_query.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=1,
        data=step_data,
    )


def sync_quotation_request_step(project_id: int) -> ProjectStep | None:
    from app.models.quotation_request import QuotationRequest

    project = db.session.get(Project, project_id)
    if project is None:
        return None

    quotation_request = (
        QuotationRequest.query
        .filter_by(project_id=project_id)
        .order_by(QuotationRequest.updated_at.desc(), QuotationRequest.id.desc())
        .first()
    )

    if quotation_request is None:
        existing_step = ProjectStep.query.filter_by(
            project_id=project_id,
            step_number=2,
        ).first()

        if existing_step is not None:
            db.session.delete(existing_step)
            db.session.flush()
        return None

    step_data = {
        "quotation_requested_date": (
            quotation_request.quotation_requested_date.isoformat()
            if hasattr(quotation_request.quotation_requested_date, "isoformat")
            else str(quotation_request.quotation_requested_date)
        ) if quotation_request.quotation_requested_date else None,
        "supplier_contacted": quotation_request.supplier_contacted,
        "remarks": quotation_request.remarks,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=2,
        data=step_data,
    )


def sync_supplier_quotation_step(project_id: int) -> ProjectStep | None:
    from app.models.supplier_quotation import SupplierQuotation

    project = db.session.get(Project, project_id)
    if project is None:
        return None

    supplier_quotation = (
        SupplierQuotation.query
        .filter_by(project_id=project_id)
        .order_by(SupplierQuotation.updated_at.desc(), SupplierQuotation.id.desc())
        .first()
    )

    if supplier_quotation is None:
        existing_step = ProjectStep.query.filter_by(
            project_id=project_id,
            step_number=3,
        ).first()

        if existing_step is not None:
            db.session.delete(existing_step)
            db.session.flush()
        return None

    val_str = (
        str(supplier_quotation.quotation_value)
        if supplier_quotation.quotation_value is not None
        else None
    )
    q_date = (
        supplier_quotation.quotation_date.isoformat()
        if hasattr(supplier_quotation.quotation_date, "isoformat")
        else str(supplier_quotation.quotation_date)
    ) if supplier_quotation.quotation_date else None

    step_data = {
        "quotation_number": supplier_quotation.quotation_number,
        "quotation_value": val_str,
        "quotation_amount": val_str,
        "quotation_date": q_date,
        "currency_unit": supplier_quotation.currency_unit,
        "validity": supplier_quotation.validity,
        "validity_days": supplier_quotation.validity,
        "incoterms": supplier_quotation.incoterms,
        "payment_terms": supplier_quotation.payment_terms,
        "delivery_period": supplier_quotation.delivery_period,
        "remark": supplier_quotation.remark,
        "remarks": supplier_quotation.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=3,
        data=step_data,
    )


def sync_customer_quotation_step(project_id: int) -> ProjectStep | None:
    from app.models.customer_quotation import CustomerQuotation

    project = db.session.get(Project, project_id)
    if project is None:
        return None

    customer_quotation = (
        CustomerQuotation.query
        .filter_by(project_id=project_id)
        .order_by(CustomerQuotation.updated_at.desc(), CustomerQuotation.id.desc())
        .first()
    )

    if customer_quotation is None:
        existing_step = ProjectStep.query.filter_by(
            project_id=project_id,
            step_number=5,
        ).first()

        if existing_step is not None:
            db.session.delete(existing_step)
            db.session.flush()
        return None

    val_str = (
        str(customer_quotation.quotation_value)
        if customer_quotation.quotation_value is not None
        else (
            str(customer_quotation.total_net_amount)
            if customer_quotation.total_net_amount is not None
            else None
        )
    )
    q_date = (
        customer_quotation.quotation_date.isoformat()
        if hasattr(customer_quotation.quotation_date, "isoformat")
        else str(customer_quotation.quotation_date)
    ) if customer_quotation.quotation_date else None

    step_data = {
        "quotation_number": customer_quotation.quotation_number or customer_quotation.qo_number,
        "quotation_amount": val_str,
        "quotation_value": val_str,
        "quotation_date": q_date,
        "sent_date": q_date,
        "currency_unit": customer_quotation.currency_unit,
        "currency_symbol": customer_quotation.currency_symbol,
        "total_net_amount": (
            str(customer_quotation.total_net_amount)
            if customer_quotation.total_net_amount is not None
            else val_str
        ),
        "validity": customer_quotation.validity,
        "validity_days": customer_quotation.validity,
        "remark": customer_quotation.remark,
        "remarks": customer_quotation.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=5,
        data=step_data,
    )


def sync_customer_tender_step(project_id: int):
    customer_tender = (
        CustomerTender.query.filter_by(project_id=project_id)
        .order_by(CustomerTender.id.desc())
        .first()
    )

    if customer_tender is None:
        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=6,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    sub_date = None
    if customer_tender.closing_date_time:
        sub_date = (
            customer_tender.closing_date_time.date().isoformat()
            if hasattr(customer_tender.closing_date_time, "date")
            else str(customer_tender.closing_date_time)[:10]
        )
    elif customer_tender.tender_date:
        sub_date = (
            customer_tender.tender_date.date().isoformat()
            if hasattr(customer_tender.tender_date, "date")
            else str(customer_tender.tender_date)[:10]
        )

    step_data = {
        "tender_number": customer_tender.tender_number,
        "submission_date": sub_date,
        "tender_title": customer_tender.tender_title,
        "officer_name": customer_tender.officer_name,
        "delivery_terms": customer_tender.delivery_terms,
        "validity": customer_tender.validity,
        "remarks": customer_tender.remark,
        "remark": customer_tender.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=6,
        data=step_data,
    )


def sync_bid_submission_step(project_id: int):
    bid_submission = (
        BidSubmission.query.filter_by(project_id=project_id)
        .order_by(BidSubmission.id.desc())
        .first()
    )

    if bid_submission is None:
        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=7,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    sub_date = None
    if bid_submission.submission_date:
        sub_date = (
            bid_submission.submission_date.date().isoformat()
            if hasattr(bid_submission.submission_date, "date")
            else str(bid_submission.submission_date)[:10]
        )

    doc_ref = bid_submission.tender_number or bid_submission.submission_number or ""

    step_data = {
        "document_reference": doc_ref,
        "tender_number": doc_ref,
        "submitted_date": sub_date,
        "submission_date": sub_date,
        "tender_title": bid_submission.tender_title,
        "tender_name": bid_submission.tender_title,
        "delivery_term": bid_submission.delivery_term,
        "delivery_terms": bid_submission.delivery_term,
        "delivery_period": bid_submission.delivery_period,
        "period": bid_submission.delivery_period,
        "payment_term": bid_submission.payment_term,
        "payment_terms": bid_submission.payment_term,
        "validity": bid_submission.validity,
        "warranty_period": bid_submission.warranty_period,
        "gst_rate": str(bid_submission.gst_rate) if bid_submission.gst_rate is not None else None,
        "remarks": bid_submission.remark,
        "remark": bid_submission.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=7,
        data=step_data,
    )


def sync_purchase_order_step(project_id: int):
    purchase_order = (
        PurchaseOrder.query.filter_by(project_id=project_id)
        .order_by(PurchaseOrder.id.desc())
        .first()
    )

    if purchase_order is None:
        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=8,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    po_date_str = None
    if purchase_order.po_date:
        po_date_str = (
            purchase_order.po_date.isoformat()
            if hasattr(purchase_order.po_date, "isoformat")
            else str(purchase_order.po_date)[:10]
        )

    po_amount_str = None
    if purchase_order.total_gross_amount is not None:
        po_amount_str = str(purchase_order.total_gross_amount)
    elif purchase_order.total_net_amount is not None:
        po_amount_str = str(purchase_order.total_net_amount)

    del_date_str = None
    if purchase_order.delivery_date:
        del_date_str = (
            purchase_order.delivery_date.isoformat()
            if hasattr(purchase_order.delivery_date, "isoformat")
            else str(purchase_order.delivery_date)[:10]
        )

    step_data = {
        "po_number": purchase_order.po_number,
        "po_no": purchase_order.po_number,
        "po_title": purchase_order.po_title,
        "po_date": po_date_str,
        "po_amount": po_amount_str,
        "poc_name": purchase_order.poc_name,
        "email": purchase_order.email,
        "contact": purchase_order.contact,
        "delivery_date": del_date_str,
        "delivery_term": purchase_order.delivery_term,
        "delivery_terms": purchase_order.delivery_term,
        "payment_terms": purchase_order.payment_terms,
        "payment_term": purchase_order.payment_terms,
        "warranty_period": purchase_order.warranty_period,
        "gst_rate": str(purchase_order.gst_rate) if purchase_order.gst_rate is not None else None,
        "gst_amount": str(purchase_order.gst_amount) if purchase_order.gst_amount is not None else None,
        "total_net_amount": str(purchase_order.total_net_amount) if purchase_order.total_net_amount is not None else None,
        "total_gross_amount": str(purchase_order.total_gross_amount) if purchase_order.total_gross_amount is not None else None,
        "remarks": purchase_order.remark,
        "remark": purchase_order.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=8,
        data=step_data,
    )


def sync_supplier_order_confirmation_step(project_id: int):
    order_confirmation = (
        SupplierOrderConfirmation.query.filter_by(project_id=project_id)
        .order_by(SupplierOrderConfirmation.id.desc())
        .first()
    )

    if order_confirmation is None:
        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=9,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    conf_date_str = None
    if order_confirmation.order_confirmation_date:
        conf_date_str = (
            order_confirmation.order_confirmation_date.isoformat()
            if hasattr(order_confirmation.order_confirmation_date, "isoformat")
            else str(order_confirmation.order_confirmation_date)[:10]
        )

    expected_delivery = order_confirmation.delivery_period or ""

    step_data = {
        "confirmation_date": conf_date_str,
        "order_confirmation_date": conf_date_str,
        "expected_delivery_date": expected_delivery,
        "delivery_period": order_confirmation.delivery_period,
        "delivery_term": order_confirmation.delivery_period,
        "shipping_terms": order_confirmation.shipping_terms,
        "shipping_term": order_confirmation.shipping_terms,
        "ref_no": order_confirmation.ref_no,
        "reference_number": order_confirmation.ref_no,
        "email": order_confirmation.email,
        "payment_terms": order_confirmation.payment_terms,
        "payment_term": order_confirmation.payment_terms,
        "warranty_period": order_confirmation.warranty_period,
        "total_amount": str(order_confirmation.total_amount) if order_confirmation.total_amount is not None else None,
        "total_net_amount": str(order_confirmation.total_net_amount) if order_confirmation.total_net_amount is not None else None,
        "remarks": order_confirmation.remark,
        "remark": order_confirmation.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=9,
        data=step_data,
    )


def sync_supplier_proforma_invoice_step(project_id: int):
    from app.models import SupplierInvoice, SupplierProformaInvoice

    supplier_inv = (
        SupplierInvoice.query.filter_by(project_id=project_id)
        .order_by(SupplierInvoice.id.desc())
        .first()
    )
    if supplier_inv is not None:
        return sync_supplier_invoice_step(project_id)

    invoice = (
        SupplierProformaInvoice.query.filter_by(project_id=project_id)
        .order_by(SupplierProformaInvoice.id.desc())
        .first()
    )

    if invoice is None:
        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=10,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    inv_date_str = None
    if invoice.proforma_invoice_date:
        inv_date_str = (
            invoice.proforma_invoice_date.isoformat()
            if hasattr(invoice.proforma_invoice_date, "isoformat")
            else str(invoice.proforma_invoice_date)[:10]
        )

    del_date_str = None
    if invoice.delivery_date:
        del_date_str = (
            invoice.delivery_date.isoformat()
            if hasattr(invoice.delivery_date, "isoformat")
            else str(invoice.delivery_date)[:10]
        )

    invoice_amt = (
        str(invoice.total_amount)
        if invoice.total_amount is not None
        else str(invoice.total_net_amount)
        if invoice.total_net_amount is not None
        else None
    )

    step_data = {
        "invoice_number": invoice.proforma_invoice_no,
        "proforma_invoice_no": invoice.proforma_invoice_no,
        "proforma_invoice_number": invoice.proforma_invoice_no,
        "invoice_date": inv_date_str,
        "proforma_invoice_date": inv_date_str,
        "invoice_amount": invoice_amt,
        "total_amount": str(invoice.total_amount) if invoice.total_amount is not None else None,
        "total_net_amount": str(invoice.total_net_amount) if invoice.total_net_amount is not None else None,
        "delivery_terms": invoice.delivery_terms,
        "delivery_term": invoice.delivery_terms,
        "delivery_period": invoice.delivery_period,
        "delivery_date": del_date_str,
        "payment_terms": invoice.payment_terms,
        "payment_term": invoice.payment_terms,
        "warranty_period": invoice.warranty_period,
        "remarks": invoice.remark,
        "remark": invoice.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=10,
        data=step_data,
    )


def sync_supplier_invoice_step(project_id: int):
    from app.models import SupplierInvoice, SupplierProformaInvoice

    invoice = (
        SupplierInvoice.query.filter_by(project_id=project_id)
        .order_by(SupplierInvoice.id.desc())
        .first()
    )

    if invoice is None:
        proforma = (
            SupplierProformaInvoice.query.filter_by(project_id=project_id)
            .order_by(SupplierProformaInvoice.id.desc())
            .first()
        )
        if proforma is not None:
            return sync_supplier_proforma_invoice_step(project_id)

        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=10,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    inv_date_str = None
    if invoice.invoice_date:
        inv_date_str = (
            invoice.invoice_date.isoformat()
            if hasattr(invoice.invoice_date, "isoformat")
            else str(invoice.invoice_date)[:10]
        )

    invoice_amt = (
        str(invoice.total_amount)
        if invoice.total_amount is not None
        else str(invoice.total_net_amount)
        if invoice.total_net_amount is not None
        else None
    )

    step_data = {
        "invoice_number": invoice.invoice_no,
        "invoice_no": invoice.invoice_no,
        "invoice_date": inv_date_str,
        "invoice_amount": invoice_amt,
        "total_amount": str(invoice.total_amount) if invoice.total_amount is not None else None,
        "total_net_amount": str(invoice.total_net_amount) if invoice.total_net_amount is not None else None,
        "delivery_terms": invoice.delivery_terms,
        "delivery_term": invoice.delivery_terms,
        "delivery_period": invoice.delivery_period,
        "payment_terms": invoice.payment_terms,
        "payment_term": invoice.payment_terms,
        "warranty_period": invoice.warranty_period,
        "remarks": invoice.remark,
        "remark": invoice.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=10,
        data=step_data,
    )


def sync_import_logistics_step(project_id: int):
    from app.models import ImportLogistics

    logistics = (
        ImportLogistics.query.filter_by(project_id=project_id)
        .order_by(ImportLogistics.id.desc())
        .first()
    )

    if logistics is None:
        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=11,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    date_str = None
    if logistics.date:
        date_str = (
            logistics.date.isoformat()
            if hasattr(logistics.date, "isoformat")
            else str(logistics.date)[:10]
        )

    tracking_num = (
        logistics.airway_bill_no
        if logistics.logistic_type == "air"
        else logistics.bill_of_lading_no
    )

    step_data = {
        "shipping_mode": logistics.logistic_type,
        "logistic_type": logistics.logistic_type,
        "tracking_number": tracking_num,
        "dispatch_date": date_str,
        "date": date_str,
        "port_of_discharge": logistics.port_of_discharge,
        "remarks": logistics.remark,
        "remark": logistics.remark,
        "airway_bill_no": logistics.airway_bill_no,
        "flight_name": logistics.flight_name,
        "flight_no": logistics.flight_no,
        "airport_of_loading": logistics.airport_of_loading,
        "bill_of_lading_no": logistics.bill_of_lading_no,
        "vessel_name": logistics.vessel_name,
        "voyage_no": logistics.voyage_no,
        "port_of_loading": logistics.port_of_loading,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=11,
        data=step_data,
    )


def sync_bill_of_entry_step(project_id: int):
    from app.models import BillOfEntry, CustomsClearance

    # If a CustomsClearance record exists, it takes precedence for step 12
    clearance = (
        CustomsClearance.query.filter_by(project_id=project_id)
        .order_by(CustomsClearance.id.desc())
        .first()
    )
    if clearance is not None:
        return sync_customs_clearance_step(project_id)

    boe = (
        BillOfEntry.query.filter_by(project_id=project_id)
        .order_by(BillOfEntry.id.desc())
        .first()
    )

    if boe is None:
        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=12,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    date_str = None
    if boe.date:
        date_str = (
            boe.date.isoformat()
            if hasattr(boe.date, "isoformat")
            else str(boe.date)[:10]
        )

    duty_val = str(boe.total_duty) if boe.total_duty is not None else None

    step_data = {
        "clearance_date": date_str,
        "date": date_str,
        "duties_paid": duty_val,
        "total_duty": duty_val,
        "bill_of_entry_no": boe.bill_of_entry_no,
        "bill_of_entry_number": boe.bill_of_entry_no,
        "total_assessable_value": str(boe.total_assessable_value) if boe.total_assessable_value is not None else None,
        "bcd": str(boe.bcd) if boe.bcd is not None else None,
        "sws": str(boe.sws) if boe.sws is not None else None,
        "igst": str(boe.igst) if boe.igst is not None else None,
        "remarks": boe.remark,
        "remark": boe.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=12,
        data=step_data,
    )


def sync_customs_clearance_step(project_id: int):
    from app.models import BillOfEntry, CustomsClearance

    clearance = (
        CustomsClearance.query.filter_by(project_id=project_id)
        .order_by(CustomsClearance.id.desc())
        .first()
    )

    if clearance is None:
        # Fall back to checking BillOfEntry
        boe = (
            BillOfEntry.query.filter_by(project_id=project_id)
            .order_by(BillOfEntry.id.desc())
            .first()
        )
        if boe is not None:
            return sync_bill_of_entry_step(project_id)

        step = (
            ProjectStep.query.filter_by(
                project_id=project_id,
                step_number=12,
            ).first()
        )
        if step is not None:
            db.session.delete(step)
            db.session.flush()
        return None

    date_str = None
    if clearance.duty_paid_date:
        date_str = (
            clearance.duty_paid_date.isoformat()
            if hasattr(clearance.duty_paid_date, "isoformat")
            else str(clearance.duty_paid_date)[:10]
        )
    elif clearance.boe_date:
        date_str = (
            clearance.boe_date.isoformat()
            if hasattr(clearance.boe_date, "isoformat")
            else str(clearance.boe_date)[:10]
        )

    duty_val = None
    if clearance.total_customs_amount is not None:
        duty_val = str(clearance.total_customs_amount)
    elif clearance.duty_amount is not None:
        duty_val = str(clearance.duty_amount)

    step_data = {
        "clearance_date": date_str,
        "date": date_str,
        "duty_paid_date": date_str,
        "duties_paid": duty_val,
        "total_duty": duty_val,
        "total_customs_amount": str(clearance.total_customs_amount) if clearance.total_customs_amount is not None else None,
        "agent_name": clearance.cha_name,
        "cha_name": clearance.cha_name,
        "bill_of_entry_no": clearance.bill_of_entry_no,
        "bill_of_entry_number": clearance.bill_of_entry_no,
        "boe_date": clearance.boe_date.isoformat() if clearance.boe_date else None,
        "customs_location": clearance.customs_location,
        "challan_no": clearance.challan_no,
        "cfs_name": clearance.cfs_name,
        "transaction_ref_no": clearance.transaction_ref_no,
        "duty_amount": str(clearance.duty_amount) if clearance.duty_amount is not None else None,
        "igst_amount": str(clearance.igst_amount) if clearance.igst_amount is not None else None,
        "other_customs_charges": str(clearance.other_customs_charges) if clearance.other_customs_charges is not None else None,
        "remarks": clearance.remark,
        "remark": clearance.remark,
    }

    return upsert_project_step_record(
        project_id=project_id,
        step_number=12,
        data=step_data,
    )

