from app.extensions.database import db
from app.models import CustomerDeliveryPackingList
from app.repositories.customer_delivery_packing_list_repository import (
    create_customer_delivery_packing_list,
    delete_customer_delivery_packing_list,
    get_customer_delivery_packing_list,
    get_project,
    list_customer_delivery_packing_lists,
    update_customer_delivery_packing_list,
)


class CustomerDeliveryPackingListError(Exception):
    """Base error for customer delivery packing list operations."""


class ProjectNotFoundError(CustomerDeliveryPackingListError):
    pass


class CustomerDeliveryPackingListNotFoundError(CustomerDeliveryPackingListError):
    pass


def create_customer_delivery_packing_list_transaction(*, data: dict) -> CustomerDeliveryPackingList:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    packing_list = create_customer_delivery_packing_list(data=data)
    db.session.flush()

    return packing_list


def get_customer_delivery_packing_list_record(packing_list_id: int) -> CustomerDeliveryPackingList:
    packing_list = get_customer_delivery_packing_list(packing_list_id)
    if packing_list is None:
        raise CustomerDeliveryPackingListNotFoundError(
            f"Customer delivery packing list with ID {packing_list_id} not found."
        )
    return packing_list


def list_customer_delivery_packing_list_records(
    *,
    project_id: int | None = None,
    packing_list_no: str | None = None,
) -> list[CustomerDeliveryPackingList]:
    return list_customer_delivery_packing_lists(
        project_id=project_id,
        packing_list_no=packing_list_no,
    )


def update_customer_delivery_packing_list_transaction(
    *,
    packing_list_id: int,
    data: dict,
) -> CustomerDeliveryPackingList:
    packing_list = get_customer_delivery_packing_list(packing_list_id)
    if packing_list is None:
        raise CustomerDeliveryPackingListNotFoundError(
            f"Customer delivery packing list with ID {packing_list_id} not found."
        )

    if "project_id" in data:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    updated_packing_list = update_customer_delivery_packing_list(
        packing_list=packing_list,
        data=data,
    )
    db.session.flush()

    return updated_packing_list


def delete_customer_delivery_packing_list_transaction(packing_list_id: int) -> list[str]:
    packing_list = get_customer_delivery_packing_list(packing_list_id)
    if packing_list is None:
        raise CustomerDeliveryPackingListNotFoundError(
            f"Customer delivery packing list with ID {packing_list_id} not found."
        )

    storage_keys = delete_customer_delivery_packing_list(packing_list_id)
    db.session.flush()
    return storage_keys

