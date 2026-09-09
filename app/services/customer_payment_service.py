from app.extensions.database import db
from app.models import CustomerPayment
from app.repositories.customer_payment_repository import (
    create_customer_payment,
    delete_customer_payment,
    get_customer_payment,
    get_project,
    list_customer_payments,
    update_customer_payment,
)


class CustomerPaymentError(Exception):
    """Base error for customer payment operations."""


class ProjectNotFoundError(CustomerPaymentError):
    pass


class CustomerPaymentNotFoundError(CustomerPaymentError):
    pass


def create_customer_payment_transaction(*, data: dict) -> CustomerPayment:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    payment = create_customer_payment(data=data)
    db.session.flush()
    return payment


def get_customer_payment_record(payment_id: int) -> CustomerPayment:
    payment = get_customer_payment(payment_id)
    if payment is None:
        raise CustomerPaymentNotFoundError(
            f"Customer payment with ID {payment_id} not found."
        )
    return payment


def list_customer_payment_records(
    *,
    project_id: int | None = None,
    invoice_no: str | None = None,
) -> list[CustomerPayment]:
    return list_customer_payments(
        project_id=project_id,
        invoice_no=invoice_no,
    )


def update_customer_payment_transaction(
    *,
    payment_id: int,
    data: dict,
) -> CustomerPayment:
    payment = get_customer_payment(payment_id)
    if payment is None:
        raise CustomerPaymentNotFoundError(
            f"Customer payment with ID {payment_id} not found."
        )

    if "project_id" in data and data["project_id"] is not None:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    updated_payment = update_customer_payment(
        payment=payment,
        data=data,
    )
    db.session.flush()
    return updated_payment


def delete_customer_payment_transaction(payment_id: int) -> list[str]:
    payment = get_customer_payment(payment_id)
    if payment is None:
        raise CustomerPaymentNotFoundError(
            f"Customer payment with ID {payment_id} not found."
        )

    storage_keys = delete_customer_payment(payment_id)
    db.session.flush()
    return storage_keys
