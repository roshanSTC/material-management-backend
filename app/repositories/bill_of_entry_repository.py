from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

from app.extensions.database import db
from app.models import BillOfEntry, Project


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_bill_of_entry(bill_of_entry_id: int) -> BillOfEntry | None:
    return db.session.get(BillOfEntry, bill_of_entry_id)


def get_bill_of_entry_by_project_id(project_id: int) -> BillOfEntry | None:
    stmt = (
        select(BillOfEntry)
        .where(BillOfEntry.project_id == project_id)
        .order_by(BillOfEntry.id.desc())
    )
    return db.session.execute(stmt).scalars().first()


def list_bills_of_entry(
    project_id: int | None = None,
    bill_of_entry_no: str | None = None,
) -> list[BillOfEntry]:
    stmt = select(BillOfEntry).order_by(BillOfEntry.id.desc())

    if project_id is not None:
        stmt = stmt.where(BillOfEntry.project_id == project_id)
    if bill_of_entry_no is not None:
        stmt = stmt.where(BillOfEntry.bill_of_entry_no == bill_of_entry_no)

    return list(db.session.execute(stmt).scalars().all())


def _parse_date_val(val) -> date | None:
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    return date.fromisoformat(s[:10])


def _parse_decimal_val(val) -> Decimal | None:
    if val is None:
        return None
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return None


def create_bill_of_entry(data: dict) -> BillOfEntry:
    record = BillOfEntry(
        project_id=data["project_id"],
        bill_of_entry_no=data["bill_of_entry_no"],
        date=_parse_date_val(data["date"]),
        total_assessable_value=_parse_decimal_val(data.get("total_assessable_value")),
        bcd=_parse_decimal_val(data.get("bcd")),
        sws=_parse_decimal_val(data.get("sws")),
        igst=_parse_decimal_val(data.get("igst")),
        total_duty=_parse_decimal_val(data.get("total_duty")),
        remark=data.get("remark"),
    )
    db.session.add(record)
    db.session.flush()
    return record


def update_bill_of_entry(record: BillOfEntry, data: dict) -> BillOfEntry:
    if "project_id" in data:
        record.project_id = data["project_id"]
    if "bill_of_entry_no" in data and data["bill_of_entry_no"] is not None:
        record.bill_of_entry_no = data["bill_of_entry_no"]
    if "date" in data and data["date"] is not None:
        record.date = _parse_date_val(data["date"])
    if "total_assessable_value" in data:
        record.total_assessable_value = _parse_decimal_val(data["total_assessable_value"])
    if "bcd" in data:
        record.bcd = _parse_decimal_val(data["bcd"])
    if "sws" in data:
        record.sws = _parse_decimal_val(data["sws"])
    if "igst" in data:
        record.igst = _parse_decimal_val(data["igst"])
    if "total_duty" in data:
        record.total_duty = _parse_decimal_val(data["total_duty"])
    if "remark" in data:
        record.remark = data["remark"]

    record.updated_at = datetime.utcnow()
    db.session.flush()
    return record


def delete_bill_of_entry(record: BillOfEntry) -> None:
    db.session.delete(record)
    db.session.flush()

