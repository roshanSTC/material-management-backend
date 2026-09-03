from app.extensions.database import db
from app.models import SupplierQuotation
from app.repositories.supplier_quotation_repository import (
    create_supplier_quotation,
    get_project,
    get_supplier,
    get_supplier_quotation,
    list_supplier_quotations,
    update_supplier_quotation,
)
from app.services.project_step_service import sync_supplier_quotation_step


class SupplierQuotationError(Exception):
    """Base error for supplier quotation operations."""


class ProjectNotFoundError(SupplierQuotationError):
    pass


class SupplierNotFoundError(SupplierQuotationError):
    pass


class SupplierProjectMismatchError(SupplierQuotationError):
    pass


class SupplierQuotationNotFoundError(SupplierQuotationError):
    pass


def list_supplier_quotation_records(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
) -> list[SupplierQuotation]:
    return list_supplier_quotations(
        project_id=project_id,
        supplier_id=supplier_id,
    )


def get_supplier_quotation_record(
    supplier_quotation_id: int,
) -> SupplierQuotation:
    supplier_quotation = get_supplier_quotation(supplier_quotation_id)
    if supplier_quotation is None:
        raise SupplierQuotationNotFoundError(
            f"Supplier quotation with id {supplier_quotation_id} was not found."
        )
    return supplier_quotation


def create_supplier_quotation_transaction(*, data: dict) -> SupplierQuotation:
    _validate_project_supplier(data["project_id"], data["supplier_id"])
    supplier_quotation = create_supplier_quotation(data=data)
    db.session.flush()
    sync_supplier_quotation_step(data["project_id"])
    return supplier_quotation


def update_supplier_quotation_transaction(
    *,
    supplier_quotation_id: int,
    data: dict,
) -> SupplierQuotation:
    supplier_quotation = get_supplier_quotation_record(supplier_quotation_id)
    previous_project_id = supplier_quotation.project_id
    project_id = data.get("project_id", supplier_quotation.project_id)
    supplier_id = data.get("supplier_id", supplier_quotation.supplier_id)
    _validate_project_supplier(project_id, supplier_id)
    update_supplier_quotation(supplier_quotation, data=data)
    db.session.flush()
    sync_supplier_quotation_step(project_id)
    if previous_project_id != project_id:
        sync_supplier_quotation_step(previous_project_id)
    return supplier_quotation


def _validate_project_supplier(project_id: int, supplier_id: int) -> None:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with id {project_id} was not found.")

    supplier = get_supplier(supplier_id)
    if supplier is None:
        raise SupplierNotFoundError(f"Supplier with id {supplier_id} was not found.")

    if project.supplier_id != supplier.id:
        raise SupplierProjectMismatchError(
            "The selected supplier does not belong to the selected project."
        )



def delete_supplier_quotation_transaction(supplier_quotation_id: int):
    supplier_quotation = get_supplier_quotation_record(
        supplier_quotation_id
    )

    if not supplier_quotation:
        raise SupplierQuotationNotFoundError(
            f"Supplier quotation {supplier_quotation_id} not found."
        )

    project_id = supplier_quotation.project_id
    db.session.delete(supplier_quotation)
    db.session.flush()
    sync_supplier_quotation_step(project_id)
    return supplier_quotation