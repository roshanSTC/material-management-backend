from datetime import date

from app.extensions.database import db
from app.models import CustomerQuery

from app.models.customer_query_item import CustomerQueryItem
from app.repositories.customer_query_repository import (
    create_customer_query,
    get_customer,
    get_project,
    get_customer_query,
    list_customer_queries,
)
from app.services.project_step_service import sync_customer_query_step


class CustomerQueryError(Exception):
    """Base error for customer query operations."""


class ProjectNotFoundError(CustomerQueryError):
    """Raised when the project does not exist."""


class CustomerNotFoundError(CustomerQueryError):
    """Raised when the customer does not exist."""


class CustomerProjectMismatchError(CustomerQueryError):
    """Raised when the customer does not belong to the project."""

class CustomerQueryNotFoundError(CustomerQueryError):
    """Raised when a customer query does not exist."""
    
    
def list_customer_query_records() -> list[CustomerQuery]:
    return list_customer_queries()


def get_customer_query_record(
    customer_query_id: int,
) -> CustomerQuery:
    customer_query = get_customer_query(customer_query_id)

    if customer_query is None:
        raise CustomerQueryNotFoundError(
            f"Customer Query with id {customer_query_id} was not found."
        )

    return customer_query


def create_customer_query_transaction(
    *,
    project_id: int,
    customer_id: int,
    qo_date,
    remark: str | None,
    items: list[dict],
) -> CustomerQuery:

    project = get_project(project_id)

    if project is None:
        raise ProjectNotFoundError(
            f"Project with id {project_id} was not found."
        )

    customer = get_customer(customer_id)

    if customer is None:
        raise CustomerNotFoundError(
            f"Customer with id {customer_id} was not found."
        )

    if project.customer_id != customer.id:
        raise CustomerProjectMismatchError(
            "The selected customer does not belong to the selected project."
        )

    if isinstance(qo_date, str):
        qo_date = date.fromisoformat(qo_date)

    customer_query = create_customer_query(
        project_id=project_id,
        customer_id=customer_id,
        qo_date=qo_date,
        remark=remark,
        items=items,
    )

    db.session.flush()

    sync_customer_query_step(project_id)

    return customer_query



def update_customer_query_transaction(
    *,
    customer_query_id: int,
    project_id: int,
    customer_id: int,
    qo_date,
    remark: str | None,
    items: list[dict],
) -> CustomerQuery:

    customer_query = get_customer_query(
        customer_query_id
    )

    if customer_query is None:
        raise CustomerQueryNotFoundError(
            f"Customer Query with id "
            f"{customer_query_id} was not found."
        )

    project = get_project(project_id)

    if project is None:
        raise ProjectNotFoundError(
            f"Project with id {project_id} was not found."
        )

    customer = get_customer(customer_id)

    if customer is None:
        raise CustomerNotFoundError(
            f"Customer with id {customer_id} was not found."
        )

    if project.customer_id != customer.id:
        raise CustomerProjectMismatchError(
            "The selected customer does not "
            "belong to the selected project."
        )

    if isinstance(qo_date, str):
        qo_date = date.fromisoformat(qo_date)

    previous_project_id = customer_query.project_id

    customer_query.project_id = project_id
    customer_query.customer_id = customer_id
    customer_query.qo_date = qo_date
    customer_query.remark = (
        remark.strip()
        if remark
        else None
    )

    customer_query.items.clear()

    for item_data in items:
        item = CustomerQueryItem(
            material_name=item_data["material_name"].strip(),
            quantity=item_data["quantity"],
        )

        customer_query.items.append(item)

    db.session.flush()

    sync_customer_query_step(project_id)
    if previous_project_id != project_id:
        sync_customer_query_step(previous_project_id)

    return customer_query


def delete_customer_query_transaction(customer_query_id: int):
    customer_query = get_customer_query_record(customer_query_id)

    if not customer_query:
        raise CustomerQueryNotFoundError(
            f"Customer query {customer_query_id} not found."
        )

    project_id = customer_query.project_id

    db.session.delete(customer_query)

    db.session.flush()

    sync_customer_query_step(project_id)

    return customer_query