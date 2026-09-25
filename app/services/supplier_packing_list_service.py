from app.extensions.database import db
from app.models import SupplierPackingList
from app.repositories.supplier_packing_list_repository import (
    create_supplier_packing_list,
    delete_supplier_packing_list,
    get_project,
    get_supplier,
    get_supplier_packing_list,
    get_supplier_packing_list_by_project,
    list_supplier_packing_lists,
    update_supplier_packing_list,
)
from app.services.project_step_service import sync_supplier_packing_list_step


class SupplierPackingListError(Exception):
    """Base error for supplier packing list operations."""


class ProjectNotFoundError(SupplierPackingListError):
    pass


class SupplierNotFoundError(SupplierPackingListError):
    pass


class SupplierPackingListNotFoundError(SupplierPackingListError):
    pass


class SupplierPackingListAlreadyExistsError(SupplierPackingListError):
    pass


def create_supplier_packing_list_transaction(*, data: dict, user_id: int | None = None) -> SupplierPackingList:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    existing = get_supplier_packing_list_by_project(project_id)
    if existing is not None:
        raise SupplierPackingListAlreadyExistsError(
            f"Supplier packing list already exists for project ID {project_id}."
        )

    supplier_id = data.get("supplier_id")
    if not supplier_id:
        supplier_id = project.supplier_id
        data["supplier_id"] = supplier_id

    if supplier_id:
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    packing_list = create_supplier_packing_list(data=data)
    db.session.flush()

    remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=10,
        remarks_data=remarks_val,
        default_user_id=user_id,
        entity_id=packing_list.id,
    )

    sync_supplier_packing_list_step(project_id)
    return packing_list


def get_supplier_packing_list_record(packing_list_id: int) -> SupplierPackingList:
    packing_list = get_supplier_packing_list(packing_list_id)
    if packing_list is None:
        raise SupplierPackingListNotFoundError(
            f"Supplier packing list with ID {packing_list_id} not found."
        )
    return packing_list


def get_latest_supplier_packing_list_record(project_id: int) -> SupplierPackingList:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    packing_list = get_supplier_packing_list_by_project(project_id)
    if packing_list is None:
        raise SupplierPackingListNotFoundError(
            f"No supplier packing list found for project ID {project_id}."
        )
    return packing_list


def list_supplier_packing_list_records(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
    packing_list_no: str | None = None,
) -> list[SupplierPackingList]:
    return list_supplier_packing_lists(
        project_id=project_id,
        supplier_id=supplier_id,
        packing_list_no=packing_list_no,
    )


def update_supplier_packing_list_transaction(
    *,
    packing_list_id: int,
    data: dict,
    user_id: int | None = None,
) -> SupplierPackingList:
    packing_list = get_supplier_packing_list_record(packing_list_id)
    previous_project_id = packing_list.project_id

    new_project_id = data.get("project_id")
    if new_project_id is not None and new_project_id != previous_project_id:
        project = get_project(new_project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {new_project_id} not found.")

        existing = get_supplier_packing_list_by_project(new_project_id)
        if existing is not None and existing.id != packing_list.id:
            raise SupplierPackingListAlreadyExistsError(
                f"Supplier packing list already exists for project ID {new_project_id}."
            )

    new_supplier_id = data.get("supplier_id")
    if new_supplier_id is not None:
        supplier = get_supplier(new_supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {new_supplier_id} not found.")

    updated = update_supplier_packing_list(packing_list=packing_list, data=data)
    db.session.flush()

    if "remarks" in data or "remark" in data:
        remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
        from app.services.step_remark_service import sync_step_remarks
        sync_step_remarks(
            project_id=updated.project_id,
            step_number=10,
            remarks_data=remarks_val,
            default_user_id=user_id,
            entity_id=updated.id,
        )

    sync_supplier_packing_list_step(updated.project_id)
    if new_project_id is not None and new_project_id != previous_project_id:
        sync_supplier_packing_list_step(previous_project_id)

    return updated


def delete_supplier_packing_list_transaction(packing_list_id: int) -> list[str]:
    packing_list = get_supplier_packing_list_record(packing_list_id)
    project_id = packing_list.project_id

    storage_keys = delete_supplier_packing_list(packing_list_id)
    db.session.flush()

    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=10,
        remarks_data=None,
        entity_id=packing_list_id,
    )

    sync_supplier_packing_list_step(project_id)
    return storage_keys

