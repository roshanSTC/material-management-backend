from datetime import datetime, timezone

from app.extensions.database import db
from app.models import Project, ProjectStep


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


