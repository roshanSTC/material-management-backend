
from app.extensions.database import db
from app.models import Customer, Project, Supplier
from app.repositories.project_repository import (
    create_project as repository_create_project,
    get_project as repository_get_project,
    list_projects as repository_list_projects,
    update_project as repository_update_project,
)


class ProjectNotFoundError(Exception):
    """Raised when a project does not exist."""


class CustomerNotFoundError(Exception):
    """Raised when the referenced customer does not exist."""


class SupplierNotFoundError(Exception):
    """Raised when the referenced supplier does not exist."""


def _validate_customer(customer_id: int) -> None:
    customer = db.session.get(Customer, customer_id)

    if customer is None:
        raise CustomerNotFoundError(
            f"Customer with id {customer_id} was not found."
        )


def _validate_supplier(supplier_id: int) -> None:
    supplier = db.session.get(Supplier, supplier_id)

    if supplier is None:
        raise SupplierNotFoundError(
            f"Supplier with id {supplier_id} was not found."
        )


def create_project(
    *,
    project_title: str,
    customer_id: int,
    supplier_id: int,
) -> Project:
    _validate_customer(customer_id)
    _validate_supplier(supplier_id)

    project = repository_create_project(
        project_title=project_title.strip(),
        customer_id=customer_id,
        supplier_id=supplier_id,
    )

    db.session.commit()

    return project


def get_project(project_id: int) -> Project:
    project = repository_get_project(project_id)

    if project is None:
        raise ProjectNotFoundError(
            f"Project with id {project_id} was not found."
        )

    return project


def list_projects() -> list[Project]:
    return repository_list_projects()


def update_project(
    project_id: int,
    *,
    project_title: str | None = None,
    customer_id: int | None = None,
    supplier_id: int | None = None,
) -> Project:
    project = get_project(project_id)

    if project_title is not None:
        project.project_title = project_title.strip()

    if customer_id is not None:
        _validate_customer(customer_id)
        project.customer_id = customer_id

    if supplier_id is not None:
        _validate_supplier(supplier_id)
        project.supplier_id = supplier_id

    project = repository_update_project(project)

    db.session.commit()

    return project

