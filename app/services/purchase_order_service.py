from app.extensions.database import db
from app.models import PurchaseOrder
from app.repositories.purchase_order_repository import (
    create_purchase_order,
    delete_purchase_order,
    get_customer,
    get_customer_tender,
    get_latest_purchase_order_for_project,
    get_project,
    get_purchase_order,
    list_purchase_orders,
    update_purchase_order,
)
from app.services.attachment_service import delete_attachment
from app.services.project_step_service import sync_purchase_order_step


class PurchaseOrderError(Exception):
    """Base error for purchase order operations."""


class ProjectNotFoundError(PurchaseOrderError):
    pass


class CustomerNotFoundError(PurchaseOrderError):
    pass


class CustomerProjectMismatchError(PurchaseOrderError):
    pass


class TenderNotFoundError(PurchaseOrderError):
    pass


class PurchaseOrderNotFoundError(PurchaseOrderError):
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

    tender_id = data.get("tender_id")
    if tender_id:
        tender = get_customer_tender(tender_id)
        if tender is None:
            raise TenderNotFoundError(f"Customer tender with ID {tender_id} not found.")

    return project_id, customer_id


def create_purchase_order_transaction(*, data: dict) -> PurchaseOrder:
    project_id, _ = _resolve_and_validate_parties(data)

    purchase_order = create_purchase_order(data=data)
    db.session.flush()

    sync_purchase_order_step(project_id)
    return purchase_order


def get_purchase_order_record(purchase_order_id: int) -> PurchaseOrder:
    po = get_purchase_order(purchase_order_id)
    if po is None:
        raise PurchaseOrderNotFoundError(f"Purchase order with ID {purchase_order_id} not found.")
    return po


def get_latest_purchase_order_record(project_id: int) -> PurchaseOrder:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    po = get_latest_purchase_order_for_project(project_id)
    if po is None:
        raise PurchaseOrderNotFoundError(f"No purchase order found for project ID {project_id}.")
    return po


def list_purchase_order_records(
    *,
    project_id: int | None = None,
) -> list[PurchaseOrder]:
    return list_purchase_orders(
        project_id=project_id,
    )


def update_purchase_order_transaction(
    *,
    purchase_order_id: int,
    data: dict,
) -> PurchaseOrder:
    purchase_order = get_purchase_order_record(purchase_order_id)
    previous_project_id = purchase_order.project_id

    if "project_id" in data or "customer_id" in data:
        check_data = {
            "project_id": data.get("project_id", purchase_order.project_id),
            "customer_id": data.get("customer_id", purchase_order.customer_id),
        }
        resolved_pid, resolved_cid = _resolve_and_validate_parties(check_data)
        if "project_id" in data:
            data["project_id"] = resolved_pid
        data["customer_id"] = resolved_cid

    if "tender_id" in data and data["tender_id"]:
        tender = get_customer_tender(data["tender_id"])
        if tender is None:
            raise TenderNotFoundError(f"Customer tender with ID {data['tender_id']} not found.")

    purchase_order = update_purchase_order(purchase_order, data=data)
    db.session.flush()

    project_id = purchase_order.project_id
    sync_purchase_order_step(project_id)
    if previous_project_id != project_id:
        sync_purchase_order_step(previous_project_id)

    return purchase_order


def delete_purchase_order_transaction(purchase_order_id: int) -> list[str]:
    purchase_order = get_purchase_order_record(purchase_order_id)
    project_id = purchase_order.project_id

    # Clean up associated attachments in DB
    storage_keys = delete_attachment(
        entity_type="purchase_order",
        entity_id=purchase_order_id,
    )

    delete_purchase_order(purchase_order)
    db.session.flush()

    sync_purchase_order_step(project_id)
    return storage_keys

