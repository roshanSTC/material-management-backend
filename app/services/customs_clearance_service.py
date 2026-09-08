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
    bill_of_entry_no: str | None = None,
    challan_no: str | None = None,
) -> list[CustomsClearance]:
    return repository.list_customs_clearances(
        project_id=project_id,
        bill_of_entry_no=bill_of_entry_no,
        challan_no=challan_no,
    )


def _compute_total_customs_amount(
    data: dict, existing: CustomsClearance | None = None
) -> Decimal | None:
    if "total_customs_amount" in data and data["total_customs_amount"] is not None:
        try:
            return Decimal(str(data["total_customs_amount"]))
        except Exception:
            pass

    duty = (
        data.get("duty_amount")
        if "duty_amount" in data
        else (existing.duty_amount if existing else None)
    )
    igst = (
        data.get("igst_amount")
        if "igst_amount" in data
        else (existing.igst_amount if existing else None)
    )
    other = (
        data.get("other_customs_charges")
        if "other_customs_charges" in data
        else (existing.other_customs_charges if existing else None)
    )

    parts = [duty, igst, other]
    if any(p is not None for p in parts):
        total = Decimal(0)
        for p in parts:
            if p is not None:
                try:
                    total += Decimal(str(p))
                except Exception:
                    pass
        return total
    return None


def create_customs_clearance_transaction(data: dict) -> CustomsClearance:
    project_id = data["project_id"]
    project = repository.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    # Try resolving bill_of_entry_id if omitted
    if not data.get("bill_of_entry_id") and data.get("bill_of_entry_no"):
        boe = (
            BillOfEntry.query.filter_by(
                project_id=project_id,
                bill_of_entry_no=data["bill_of_entry_no"],
            )
            .order_by(BillOfEntry.id.desc())
            .first()
        )
        if boe:
            data["bill_of_entry_id"] = boe.id

    if data.get("total_customs_amount") is None:
        computed_total = _compute_total_customs_amount(data)
        if computed_total is not None:
            data["total_customs_amount"] = computed_total

    try:
        record = repository.create_customs_clearance(data)
        try:
            sync_customs_clearance_step(project_id)
        except Exception:
            pass
        db.session.commit()
        return record
    except Exception:
        db.session.rollback()
        raise


def update_customs_clearance_transaction(
    clearance_id: int,
    data: dict,
) -> CustomsClearance:
    record = repository.get_customs_clearance(clearance_id)
    if not record:
        raise CustomsClearanceNotFoundError(
            f"Customs clearance with ID {clearance_id} not found."
        )

    target_project_id = data.get("project_id", record.project_id)
    if "project_id" in data and data["project_id"] != record.project_id:
        project = repository.get_project(data["project_id"])
        if not project:
            raise ProjectNotFoundError(
                f"Project with ID {data['project_id']} not found."
            )

    boe_no = data.get("bill_of_entry_no", record.bill_of_entry_no)
    if boe_no and not data.get("bill_of_entry_id"):
        boe = (
            BillOfEntry.query.filter_by(
                project_id=target_project_id,
                bill_of_entry_no=boe_no,
            )
            .order_by(BillOfEntry.id.desc())
            .first()
        )
        if boe:
            data["bill_of_entry_id"] = boe.id

    if data.get("total_customs_amount") is None and (
        "duty_amount" in data
        or "igst_amount" in data
        or "other_customs_charges" in data
    ):
        computed_total = _compute_total_customs_amount(data, existing=record)
        if computed_total is not None:
            data["total_customs_amount"] = computed_total

    try:
        updated = repository.update_customs_clearance(record, data)
        try:
            sync_customs_clearance_step(updated.project_id)
        except Exception:
            pass
        db.session.commit()
        return updated
    except Exception:
        db.session.rollback()
        raise


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

    try:
        for att in attachments:
            db.session.delete(att)
        repository.delete_customs_clearance(record)
        try:
            sync_customs_clearance_step(project_id)
        except Exception:
            pass
        db.session.commit()
        return storage_keys
    except Exception:
        db.session.rollback()
        raise
