from app.extensions.database import db
from app.models import TransportDetail
from app.repositories.transport_detail_repository import (
    create_transport_detail,
    delete_transport_detail,
    get_project,
    get_transport_detail,
    list_transport_details,
    update_transport_detail,
)


class TransportDetailError(Exception):
    pass


class ProjectNotFoundError(TransportDetailError):
    pass


class TransportDetailNotFoundError(TransportDetailError):
    pass


def create_transport_detail_transaction(*, data: dict) -> TransportDetail:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    detail = create_transport_detail(data=data)
    db.session.flush()

    return detail


def get_transport_detail_record(transport_detail_id: int) -> TransportDetail:
    detail = get_transport_detail(transport_detail_id)
    if detail is None:
        raise TransportDetailNotFoundError(
            f"Transport detail with ID {transport_detail_id} not found."
        )
    return detail


def list_transport_detail_records(
    *,
    project_id: int | None = None,
    transport_mode: str | None = None,
    lr_no: str | None = None,
) -> list[TransportDetail]:
    return list_transport_details(
        project_id=project_id,
        transport_mode=transport_mode,
        lr_no=lr_no,
    )


def update_transport_detail_transaction(
    *,
    transport_detail_id: int,
    data: dict,
) -> TransportDetail:
    detail = get_transport_detail(transport_detail_id)
    if detail is None:
        raise TransportDetailNotFoundError(
            f"Transport detail with ID {transport_detail_id} not found."
        )

    if "project_id" in data:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    updated_detail = update_transport_detail(
        detail=detail,
        data=data,
    )
    db.session.flush()

    return updated_detail


def delete_transport_detail_transaction(transport_detail_id: int) -> list[str]:
    detail = get_transport_detail(transport_detail_id)
    if detail is None:
        raise TransportDetailNotFoundError(
            f"Transport detail with ID {transport_detail_id} not found."
        )

    storage_keys = delete_transport_detail(transport_detail_id)
    db.session.flush()
    return storage_keys
