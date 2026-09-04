from app.extensions.database import db
from app.models import CustomerTender
from app.repositories.customer_tender_repository import (
    create_customer_tender,
    delete_customer_tender,
    get_customer,
    get_customer_tender,
    get_project,
    list_customer_tenders,
    update_customer_tender,
)
from app.services.attachment_service import delete_attachment
from app.services.project_step_service import sync_customer_tender_step


class CustomerTenderError(Exception):
    """Base error for customer tender operations."""


class ProjectNotFoundError(CustomerTenderError):
    pass


class CustomerNotFoundError(CustomerTenderError):
    pass


class CustomerProjectMismatchError(CustomerTenderError):
    pass


class CustomerTenderNotFoundError(CustomerTenderError):
    pass


def _resolve_and_validate_parties(data: dict) -> tuple[int, int]:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    customer_id = data.get("customer_id")
    if customer_id is None or customer_id == 0:
        customer_id = project.customer_id
        data["customer_id"] = customer_id

    customer = get_customer(customer_id)
    if customer is None:
        raise CustomerNotFoundError(f"Customer with ID {customer_id} not found.")

    if project.customer_id and project.customer_id != customer_id:
        raise CustomerProjectMismatchError(
            f"Customer ID {customer_id} does not match project's customer ID {project.customer_id}."
        )

    return project_id, customer_id


def create_customer_tender_transaction(*, data: dict) -> CustomerTender:
    project_id, _ = _resolve_and_validate_parties(data)

    customer_tender = create_customer_tender(data=data)
    db.session.flush()

    sync_customer_tender_step(project_id)
    return customer_tender


def get_customer_tender_record(customer_tender_id: int) -> CustomerTender:
    tender = get_customer_tender(customer_tender_id)
    if tender is None:
        raise CustomerTenderNotFoundError(f"Customer tender with ID {customer_tender_id} not found.")
    return tender


def list_customer_tender_records(
    *,
    project_id: int | None = None,
) -> list[CustomerTender]:
    return list_customer_tenders(
        project_id=project_id,
    )


def update_customer_tender_transaction(
    *,
    customer_tender_id: int,
    data: dict,
) -> CustomerTender:
    customer_tender = get_customer_tender_record(customer_tender_id)
    previous_project_id = customer_tender.project_id

    if "project_id" in data or "customer_id" in data:
        check_data = {
            "project_id": data.get("project_id", customer_tender.project_id),
            "customer_id": data.get("customer_id", customer_tender.customer_id),
        }
        resolved_pid, resolved_cid = _resolve_and_validate_parties(check_data)
        if "project_id" in data:
            data["project_id"] = resolved_pid
        data["customer_id"] = resolved_cid

    customer_tender = update_customer_tender(customer_tender, data=data)
    db.session.flush()

    project_id = customer_tender.project_id
    sync_customer_tender_step(project_id)
    if previous_project_id != project_id:
        sync_customer_tender_step(previous_project_id)

    return customer_tender


def delete_customer_tender_transaction(customer_tender_id: int) -> list[str]:
    customer_tender = get_customer_tender_record(customer_tender_id)
    project_id = customer_tender.project_id

    # Clean up associated attachments in DB
    storage_keys = delete_attachment(
        entity_type="customer_tender",
        entity_id=customer_tender_id,
    )

    delete_customer_tender(customer_tender)
    db.session.flush()

    sync_customer_tender_step(project_id)
    return storage_keys

