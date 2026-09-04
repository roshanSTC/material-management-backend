from app.extensions.database import db
from app.models import CustomerQuotation
from app.repositories.customer_quotation_repository import (
    create_customer_quotation,
    delete_customer_quotation,
    get_customer,
    get_customer_quotation,
    get_project,
    list_customer_quotations,
    update_customer_quotation,
)
from app.services.attachment_service import delete_attachment, list_attachments
from app.services.project_step_service import sync_customer_quotation_step


class CustomerQuotationError(Exception):
    """Base error for customer quotation operations."""


class ProjectNotFoundError(CustomerQuotationError):
    pass


class CustomerNotFoundError(CustomerQuotationError):
    pass


class CustomerProjectMismatchError(CustomerQuotationError):
    pass


class CustomerQuotationNotFoundError(CustomerQuotationError):
    pass


def _validate_project_customer(project_id: int, customer_id: int | None) -> int:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with id {project_id} was not found.")

    # If customer_id is 0 or None, automatically infer from the project
    if not customer_id:
        resolved_customer_id = project.customer_id
    else:
        resolved_customer_id = customer_id

    customer = get_customer(resolved_customer_id)
    if customer is None:
        raise CustomerNotFoundError(f"Customer with id {resolved_customer_id} was not found.")

    if project.customer_id != customer.id:
        raise CustomerProjectMismatchError(
            "The selected customer does not belong to the selected project."
        )

    return resolved_customer_id


def list_customer_quotation_records(
    *,
    project_id: int | None = None,
    
) -> list[CustomerQuotation]:
    return list_customer_quotations(
        project_id=project_id,
    )


def get_customer_quotation_record(
    customer_quotation_id: int,
) -> CustomerQuotation:
    customer_quotation = get_customer_quotation(customer_quotation_id)
    if customer_quotation is None:
        raise CustomerQuotationNotFoundError(
            f"Customer quotation with id {customer_quotation_id} was not found."
        )
    return customer_quotation


def create_customer_quotation_transaction(*, data: dict) -> CustomerQuotation:
    customer_id = data.get("customer_id")
    resolved_customer_id = _validate_project_customer(data["project_id"], customer_id)
    data["customer_id"] = resolved_customer_id

    customer_quotation = create_customer_quotation(data=data)
    db.session.flush()
    sync_customer_quotation_step(data["project_id"])
    return customer_quotation


def update_customer_quotation_transaction(
    *,
    customer_quotation_id: int,
    data: dict,
) -> CustomerQuotation:
    customer_quotation = get_customer_quotation_record(customer_quotation_id)
    previous_project_id = customer_quotation.project_id
    project_id = data.get("project_id", customer_quotation.project_id)
    customer_id = data.get("customer_id", customer_quotation.customer_id)

    resolved_customer_id = _validate_project_customer(project_id, customer_id)
    data["customer_id"] = resolved_customer_id

    update_customer_quotation(customer_quotation, data=data)
    db.session.flush()
    sync_customer_quotation_step(project_id)
    if previous_project_id != project_id:
        sync_customer_quotation_step(previous_project_id)
    return customer_quotation


def delete_customer_quotation_transaction(customer_quotation_id: int) -> None:
    customer_quotation = get_customer_quotation_record(customer_quotation_id)
    project_id = customer_quotation.project_id

    # Clean up associated attachments
    attachments = list_attachments(
        entity_type="customer_quotation",
        entity_id=customer_quotation_id,
    )
    for attachment in attachments:
        delete_attachment(attachment.id)

    delete_customer_quotation(customer_quotation)
    db.session.flush()
    sync_customer_quotation_step(project_id)

