from app.extensions.database import db
from app.models import SupplierOrderConfirmation
from app.repositories.supplier_order_confirmation_repository import (
    create_supplier_order_confirmation,
    delete_supplier_order_confirmation,
    get_project,
    get_purchase_order,
    get_supplier,
    get_supplier_order_confirmation,
    get_supplier_order_confirmation_by_project,
    list_supplier_order_confirmations,
    update_supplier_order_confirmation,
)
from app.services.attachment_service import delete_attachment
from app.services.project_step_service import sync_supplier_order_confirmation_step


class OrderConfirmationError(Exception):
    """Base error for order confirmation operations."""


class ProjectNotFoundError(OrderConfirmationError):
    pass


class SupplierNotFoundError(OrderConfirmationError):
    pass


class OrderConfirmationNotFoundError(OrderConfirmationError):
    pass


class OrderConfirmationAlreadyExistsError(OrderConfirmationError):
    pass


def create_supplier_order_confirmation_transaction(*, data: dict) -> SupplierOrderConfirmation:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    existing = get_supplier_order_confirmation_by_project(project_id)
    if existing is not None:
        raise OrderConfirmationAlreadyExistsError(
            f"Order confirmation already exists for project ID {project_id}."
        )

    supplier_id = data.get("supplier_id")
    if not supplier_id:
        supplier_id = project.supplier_id
        data["supplier_id"] = supplier_id

    if supplier_id:
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    confirmation = create_supplier_order_confirmation(data=data)
    db.session.flush()

    sync_supplier_order_confirmation_step(project_id)
    return confirmation


def get_supplier_order_confirmation_record(confirmation_id: int) -> SupplierOrderConfirmation:
    confirmation = get_supplier_order_confirmation(confirmation_id)
    if confirmation is None:
        raise OrderConfirmationNotFoundError(
            f"Supplier order confirmation with ID {confirmation_id} not found."
        )
    return confirmation


def get_latest_supplier_order_confirmation_record(project_id: int) -> SupplierOrderConfirmation:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    confirmation = get_supplier_order_confirmation_by_project(project_id)
    if confirmation is None:
        raise OrderConfirmationNotFoundError(
            f"No order confirmation found for project ID {project_id}."
        )
    return confirmation


def list_supplier_order_confirmation_records(
    *,
    project_id: int | None = None,
) -> list[SupplierOrderConfirmation]:
    return list_supplier_order_confirmations(
        project_id=project_id,
    )


def update_supplier_order_confirmation_transaction(
    *,
    confirmation_id: int,
    data: dict,
) -> SupplierOrderConfirmation:
    confirmation = get_supplier_order_confirmation_record(confirmation_id)
    previous_project_id = confirmation.project_id

    new_project_id = data.get("project_id")
    if new_project_id is not None and new_project_id != previous_project_id:
        project = get_project(new_project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {new_project_id} not found.")

        existing = get_supplier_order_confirmation_by_project(new_project_id)
        if existing is not None and existing.id != confirmation.id:
            raise OrderConfirmationAlreadyExistsError(
                f"Order confirmation already exists for project ID {new_project_id}."
            )

        if "supplier_id" not in data or not data.get("supplier_id"):
            data["supplier_id"] = project.supplier_id

    supplier_id = data.get("supplier_id")
    if supplier_id:
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    confirmation = update_supplier_order_confirmation(confirmation, data=data)
    db.session.flush()

    current_project_id = confirmation.project_id
    sync_supplier_order_confirmation_step(current_project_id)
    if previous_project_id != current_project_id:
        sync_supplier_order_confirmation_step(previous_project_id)

    return confirmation


def delete_supplier_order_confirmation_transaction(confirmation_id: int) -> list[str]:
    confirmation = get_supplier_order_confirmation_record(confirmation_id)
    project_id = confirmation.project_id

    keys1 = delete_attachment(
        entity_type="order_confirmation",
        entity_id=confirmation_id,
    )
    keys2 = delete_attachment(
        entity_type="supplier_order_confirmation",
        entity_id=confirmation_id,
    )

    delete_supplier_order_confirmation(confirmation)
    db.session.flush()

    sync_supplier_order_confirmation_step(project_id)
    return keys1 + keys2

