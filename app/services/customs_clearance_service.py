from decimal import Decimal

from app.extensions.database import db
from app.models import Attachment, BillOfEntry, CustomsClearance
from app.repositories import customs_clearance_repository as repository
from app.services.project_step_service import sync_customs_clearance_step


class CustomsClearanceError(Exception):
    pass


class CustomsClearanceNotFoundError(CustomsClearanceError):
    pass


class ProjectNotFoundError(CustomsClearanceError):
    pass


def get_customs_clearance_record(clearance_id: int) -> CustomsClearance:
    record = repository.get_customs_clearance(clearance_id)
    if not record:
        raise CustomsClearanceNotFoundError(
            f"Customs clearance with ID {clearance_id} not found."
        )
    return record


def list_customs_clearances_records(
    project_id: int | None = None,
    invoice_no: str | None = None,
) -> list[CustomsClearance]:
    return repository.list_customs_clearances(
        project_id=project_id,
        invoice_no=invoice_no,
    )


def create_customs_clearance_transaction(data: dict, user_id: int | None = None) -> CustomsClearance:
    project_id = data["project_id"]
    project = repository.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    if not data.get("bill_of_entry_id"):
        boe = (
            BillOfEntry.query.filter_by(project_id=project_id)
            .order_by(BillOfEntry.id.desc())
            .first()
        )
        if boe:
            data["bill_of_entry_id"] = boe.id

    record = repository.create_customs_clearance(data)
    try:
        sync_customs_clearance_step(project_id)
    except Exception:
        pass
    db.session.flush()

    remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=12,
        remarks_data=remarks_val,
        default_user_id=user_id,
        entity_id=record.id,
    )

    return record


def update_customs_clearance_transaction(
    clearance_id: int,
    data: dict,
    user_id: int | None = None,
) -> CustomsClearance:
    record = repository.get_customs_clearance(clearance_id)
    if not record:
        raise CustomsClearanceNotFoundError(
            f"Customs clearance with ID {clearance_id} not found."
        )

    if "project_id" in data and data["project_id"] != record.project_id:
        project = repository.get_project(data["project_id"])
        if not project:
            raise ProjectNotFoundError(
                f"Project with ID {data['project_id']} not found."
            )

    updated = repository.update_customs_clearance(record, data)
    try:
        sync_customs_clearance_step(updated.project_id)
    except Exception:
        pass
    db.session.flush()

    if "remarks" in data or "remark" in data:
        remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
        from app.services.step_remark_service import sync_step_remarks
        sync_step_remarks(
            project_id=updated.project_id,
            step_number=12,
            remarks_data=remarks_val,
            default_user_id=user_id,
            entity_id=updated.id,
        )

    return updated


def delete_customs_clearance_transaction(clearance_id: int) -> list[str]:
    record = repository.get_customs_clearance(clearance_id)
    if not record:
        raise CustomsClearanceNotFoundError(
            f"Customs clearance with ID {clearance_id} not found."
        )

    project_id = record.project_id

    attachments = (
        Attachment.query.filter_by(
            entity_type="customs_clearance",
            entity_id=record.id,
        ).all()
    )
    storage_keys = [att.storage_key for att in attachments if att.storage_key]

    for att in attachments:
        db.session.delete(att)
    repository.delete_customs_clearance(record)
    try:
        sync_customs_clearance_step(project_id)
    except Exception:
        pass
    db.session.flush()

    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=12,
        remarks_data=None,
        entity_id=clearance_id,
    )

    return storage_keys
