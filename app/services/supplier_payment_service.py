from app.extensions.database import db
from app.models import SupplierPayment
from app.repositories.supplier_payment_repository import (
    create_supplier_payment,
    delete_supplier_payment,
    get_project,
    get_supplier,
    get_supplier_payment,
    list_supplier_payments,
    update_supplier_payment,
)


class SupplierPaymentError(Exception):
    """Base error for supplier payment operations."""


class ProjectNotFoundError(SupplierPaymentError):
    pass


class SupplierNotFoundError(SupplierPaymentError):
    pass


class SupplierPaymentNotFoundError(SupplierPaymentError):
    pass


def create_supplier_payment_transaction(*, data: dict) -> SupplierPayment:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    supplier_id = data.get("supplier_id")
    if supplier_id is None:
        data["supplier_id"] = project.supplier_id
    else:
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    payment = create_supplier_payment(data=data)
    db.session.flush()
    return payment


def get_supplier_payment_record(payment_id: int) -> SupplierPayment:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        raise SupplierPaymentNotFoundError(
            f"Supplier payment with ID {payment_id} not found."
        )
    return payment


def list_supplier_payment_records(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
    currency: str | None = None,
) -> list[SupplierPayment]:
    return list_supplier_payments(
        project_id=project_id,
        supplier_id=supplier_id,
        currency=currency,
    )


def update_supplier_payment_transaction(
    *,
    payment_id: int,
    data: dict,
) -> SupplierPayment:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        raise SupplierPaymentNotFoundError(
            f"Supplier payment with ID {payment_id} not found."
        )

    if "project_id" in data and data["project_id"] is not None:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    if "supplier_id" in data and data["supplier_id"] is not None:
        supplier_id = data["supplier_id"]
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    updated_payment = update_supplier_payment(
        payment=payment,
        data=data,
    )
    db.session.flush()
    return updated_payment


def delete_supplier_payment_transaction(payment_id: int) -> list[str]:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        raise SupplierPaymentNotFoundError(
            f"Supplier payment with ID {payment_id} not found."
        )

    storage_keys = delete_supplier_payment(payment_id)
    db.session.flush()
    return storage_keys
