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
            "query_description",
            "query_date",
            "remarks",
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
            "quotation_amount",
            "quotation_date",
            "validity_days",
            "remarks",
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