from app.extensions.database import db
from app.models import CustomerQuery

from app.repositories.customer_query_repository import (
    create_customer_query,
    get_customer,
    get_project,
    get_customer_query,
    list_customer_queries,
)


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

    customer_query = create_customer_query(
        project_id=project_id,
        customer_id=customer_id,
        qo_date=qo_date,
        remark=remark,
        items=items,
    )

    db.session.flush()

    return customer_query