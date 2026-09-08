from app.extensions.database import db
from app.models import SupplierProformaInvoice
from app.repositories.supplier_proforma_invoice_repository import (
    create_supplier_proforma_invoice,
    delete_supplier_proforma_invoice,
    get_order_confirmation,
    get_project,
    get_supplier,
    get_supplier_proforma_invoice,
    get_supplier_proforma_invoice_by_project,
    list_supplier_proforma_invoices,
    update_supplier_proforma_invoice,
)
from app.services.project_step_service import sync_supplier_proforma_invoice_step


class ProformaInvoiceError(Exception):
    """Base error for proforma invoice operations."""


class ProjectNotFoundError(ProformaInvoiceError):
    pass


class SupplierNotFoundError(ProformaInvoiceError):
    pass


class ProformaInvoiceNotFoundError(ProformaInvoiceError):
    pass


class ProformaInvoiceAlreadyExistsError(ProformaInvoiceError):
    pass


def create_supplier_proforma_invoice_transaction(*, data: dict) -> SupplierProformaInvoice:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    existing = get_supplier_proforma_invoice_by_project(project_id)
    if existing is not None:
        raise ProformaInvoiceAlreadyExistsError(
            f"Proforma invoice already exists for project ID {project_id}."
        )

    supplier_id = data.get("supplier_id")
    if not supplier_id:
        supplier_id = project.supplier_id
        data["supplier_id"] = supplier_id

    if supplier_id:
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    order_conf_id = data.get("order_confirmation_id")
    if order_conf_id:
        order_conf = get_order_confirmation(order_conf_id)
        if order_conf is None:
            data["order_confirmation_id"] = None

    invoice = create_supplier_proforma_invoice(data=data)
    db.session.flush()

    sync_supplier_proforma_invoice_step(project_id)
    return invoice


def get_supplier_proforma_invoice_record(invoice_id: int) -> SupplierProformaInvoice:
    invoice = get_supplier_proforma_invoice(invoice_id)
    if invoice is None:
        raise ProformaInvoiceNotFoundError(
            f"Supplier proforma invoice with ID {invoice_id} not found."
        )
    return invoice


def get_latest_supplier_proforma_invoice_record(project_id: int) -> SupplierProformaInvoice:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    invoice = get_supplier_proforma_invoice_by_project(project_id)
    if invoice is None:
        raise ProformaInvoiceNotFoundError(
            f"No proforma invoice found for project ID {project_id}."
        )
    return invoice


def list_supplier_proforma_invoice_records(
    *,
    project_id: int | None = None,
) -> list[SupplierProformaInvoice]:
    return list_supplier_proforma_invoices(
        project_id=project_id,
    )


def update_supplier_proforma_invoice_transaction(
    *,
    invoice_id: int,
    data: dict,
) -> SupplierProformaInvoice:
    invoice = get_supplier_proforma_invoice_record(invoice_id)
    previous_project_id = invoice.project_id

    new_project_id = data.get("project_id")
    if new_project_id is not None and new_project_id != previous_project_id:
        project = get_project(new_project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {new_project_id} not found.")

        existing = get_supplier_proforma_invoice_by_project(new_project_id)
        if existing is not None and existing.id != invoice.id:
            raise ProformaInvoiceAlreadyExistsError(
                f"Proforma invoice already exists for project ID {new_project_id}."
            )

    new_supplier_id = data.get("supplier_id")
    if new_supplier_id is not None:
        supplier = get_supplier(new_supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {new_supplier_id} not found.")

    updated_invoice = update_supplier_proforma_invoice(invoice=invoice, data=data)
    db.session.flush()

    sync_supplier_proforma_invoice_step(updated_invoice.project_id)
    if new_project_id is not None and new_project_id != previous_project_id:
        sync_supplier_proforma_invoice_step(previous_project_id)

    return updated_invoice


def delete_supplier_proforma_invoice_transaction(invoice_id: int) -> list[str]:
    invoice = get_supplier_proforma_invoice_record(invoice_id)
    project_id = invoice.project_id

    storage_keys = delete_supplier_proforma_invoice(invoice_id)
    db.session.flush()

    sync_supplier_proforma_invoice_step(project_id)
    return storage_keys

