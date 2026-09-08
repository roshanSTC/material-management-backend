from decimal import Decimal

from app.extensions.database import db
from app.models import Attachment, BillOfEntry
from app.repositories import bill_of_entry_repository as repository
from app.services.project_step_service import sync_bill_of_entry_step


class BillOfEntryError(Exception):
    pass


class BillOfEntryNotFoundError(BillOfEntryError):
    pass


class ProjectNotFoundError(BillOfEntryError):
    pass


def get_bill_of_entry_record(bill_of_entry_id: int) -> BillOfEntry:
    record = repository.get_bill_of_entry(bill_of_entry_id)
    if not record:
        raise BillOfEntryNotFoundError(
            f"Bill of Entry with ID {bill_of_entry_id} not found."
        )
    return record


def list_bills_of_entry_records(
    project_id: int | None = None,
    bill_of_entry_no: str | None = None,
) -> list[BillOfEntry]:
    return repository.list_bills_of_entry(
        project_id=project_id,
        bill_of_entry_no=bill_of_entry_no,
    )


def _compute_total_duty(data: dict, existing: BillOfEntry | None = None) -> Decimal | None:
    if "total_duty" in data and data["total_duty"] is not None:
        try:
            return Decimal(str(data["total_duty"]))
        except Exception:
            pass

    bcd = data.get("bcd") if "bcd" in data else (existing.bcd if existing else None)
    sws = data.get("sws") if "sws" in data else (existing.sws if existing else None)
    igst = data.get("igst") if "igst" in data else (existing.igst if existing else None)

    parts = [bcd, sws, igst]
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


def create_bill_of_entry_transaction(data: dict) -> BillOfEntry:
    project_id = data["project_id"]
    project = repository.get_project(project_id)
    if not project:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    if data.get("total_duty") is None:
        computed_duty = _compute_total_duty(data)
        if computed_duty is not None:
            data["total_duty"] = computed_duty

    record = repository.create_bill_of_entry(data)
    try:
        sync_bill_of_entry_step(project_id)
    except Exception:
        pass
    db.session.flush()
    return record


def update_bill_of_entry_transaction(
    bill_of_entry_id: int,
    data: dict,
) -> BillOfEntry:
    record = repository.get_bill_of_entry(bill_of_entry_id)
    if not record:
        raise BillOfEntryNotFoundError(
            f"Bill of Entry with ID {bill_of_entry_id} not found."
        )

    if "project_id" in data and data["project_id"] != record.project_id:
        project = repository.get_project(data["project_id"])
        if not project:
            raise ProjectNotFoundError(
                f"Project with ID {data['project_id']} not found."
            )

    if data.get("total_duty") is None and ("bcd" in data or "sws" in data or "igst" in data):
        computed_duty = _compute_total_duty(data, existing=record)
        if computed_duty is not None:
            data["total_duty"] = computed_duty

    updated = repository.update_bill_of_entry(record, data)
    try:
        sync_bill_of_entry_step(updated.project_id)
    except Exception:
        pass
    db.session.flush()
    return updated


def delete_bill_of_entry_transaction(bill_of_entry_id: int) -> list[str]:
    record = repository.get_bill_of_entry(bill_of_entry_id)
    if not record:
        raise BillOfEntryNotFoundError(
            f"Bill of Entry with ID {bill_of_entry_id} not found."
        )

    project_id = record.project_id

    attachments = (
        Attachment.query.filter_by(
            entity_type="bill_of_entry",
            entity_id=record.id,
        ).all()
    )
    storage_keys = [att.storage_key for att in attachments if att.storage_key]

    for att in attachments:
        db.session.delete(att)
    repository.delete_bill_of_entry(record)
    try:
        sync_bill_of_entry_step(project_id)
    except Exception:
        pass
    db.session.flush()
    return storage_keys

