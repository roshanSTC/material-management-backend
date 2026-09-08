from app.extensions.database import db
from app.models import SupplierInvoice
from app.repositories.supplier_invoice_repository import (
    create_supplier_invoice,
    delete_supplier_invoice,
    get_project,
    get_supplier,
    get_supplier_invoice,
    get_supplier_invoice_by_project,
    list_supplier_invoices,
    update_supplier_invoice,
)
from app.services.project_step_service import sync_supplier_invoice_step


class SupplierInvoiceError(Exception):
    """Base error for supplier invoice operations."""


class ProjectNotFoundError(SupplierInvoiceError):
    pass


class SupplierNotFoundError(SupplierInvoiceError):
    pass


class SupplierInvoiceNotFoundError(SupplierInvoiceError):
    pass


class SupplierInvoiceAlreadyExistsError(SupplierInvoiceError):
    pass


def create_supplier_invoice_transaction(*, data: dict) -> SupplierInvoice:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    existing = get_supplier_invoice_by_project(project_id)
    if existing is not None:
        raise SupplierInvoiceAlreadyExistsError(
            f"Supplier invoice already exists for project ID {project_id}."
        )

    supplier_id = data.get("supplier_id")
    if not supplier_id:
        supplier_id = project.supplier_id
        data["supplier_id"] = supplier_id

    if supplier_id:
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    invoice = create_supplier_invoice(data=data)
    db.session.flush()

    sync_supplier_invoice_step(project_id)
    return invoice


def get_supplier_invoice_record(invoice_id: int) -> SupplierInvoice:
    invoice = get_supplier_invoice(invoice_id)
    if invoice is None:
        raise SupplierInvoiceNotFoundError(
            f"Supplier invoice with ID {invoice_id} not found."
        )
    return invoice


def get_latest_supplier_invoice_record(project_id: int) -> SupplierInvoice:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    invoice = get_supplier_invoice_by_project(project_id)
    if invoice is None:
        raise SupplierInvoiceNotFoundError(
            f"No supplier invoice found for project ID {project_id}."
        )
    return invoice


def list_supplier_invoice_records(
    *,
    project_id: int | None = None,
) -> list[SupplierInvoice]:
    return list_supplier_invoices(
        project_id=project_id,
    )


def update_supplier_invoice_transaction(
    *,
    invoice_id: int,
    data: dict,
) -> SupplierInvoice:
    invoice = get_supplier_invoice_record(invoice_id)
    previous_project_id = invoice.project_id

    new_project_id = data.get("project_id")
    if new_project_id is not None and new_project_id != previous_project_id:
        project = get_project(new_project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {new_project_id} not found.")

        existing = get_supplier_invoice_by_project(new_project_id)
        if existing is not None and existing.id != invoice.id:
            raise SupplierInvoiceAlreadyExistsError(
                f"Supplier invoice already exists for project ID {new_project_id}."
            )

    new_supplier_id = data.get("supplier_id")
    if new_supplier_id is not None:
        supplier = get_supplier(new_supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {new_supplier_id} not found.")

    updated_invoice = update_supplier_invoice(invoice=invoice, data=data)
    db.session.flush()

    sync_supplier_invoice_step(updated_invoice.project_id)
    if new_project_id is not None and new_project_id != previous_project_id:
        sync_supplier_invoice_step(previous_project_id)

    return updated_invoice


def delete_supplier_invoice_transaction(invoice_id: int) -> list[str]:
    invoice = get_supplier_invoice_record(invoice_id)
    project_id = invoice.project_id

    storage_keys = delete_supplier_invoice(invoice_id)
    db.session.flush()

    sync_supplier_invoice_step(project_id)
    return storage_keys

