from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

from app.extensions.database import db
from app.models import CustomsClearance, Project


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_customs_clearance(clearance_id: int) -> CustomsClearance | None:
    return db.session.get(CustomsClearance, clearance_id)


def get_customs_clearance_by_project_id(project_id: int) -> CustomsClearance | None:
    stmt = (
        select(CustomsClearance)
        .where(CustomsClearance.project_id == project_id)
        .order_by(CustomsClearance.id.desc())
    )
    return db.session.execute(stmt).scalars().first()


def list_customs_clearances(
    project_id: int | None = None,
    bill_of_entry_no: str | None = None,
    challan_no: str | None = None,
) -> list[CustomsClearance]:
    stmt = select(CustomsClearance).order_by(CustomsClearance.id.desc())

    if project_id is not None:
        stmt = stmt.where(CustomsClearance.project_id == project_id)
    if bill_of_entry_no is not None:
        stmt = stmt.where(CustomsClearance.bill_of_entry_no == bill_of_entry_no)
    if challan_no is not None:
        stmt = stmt.where(CustomsClearance.challan_no == challan_no)

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


def create_customs_clearance(data: dict) -> CustomsClearance:
    record = CustomsClearance(
        project_id=data["project_id"],
        bill_of_entry_id=data.get("bill_of_entry_id"),
        cha_name=data["cha_name"],
        bill_of_entry_no=data.get("bill_of_entry_no"),
        boe_date=_parse_date_val(data.get("boe_date")),
        customs_location=data.get("customs_location"),
        duty_paid_date=_parse_date_val(data.get("duty_paid_date")),
        challan_no=data.get("challan_no"),
        cfs_name=data.get("cfs_name"),
        transaction_ref_no=data.get("transaction_ref_no"),
        duty_amount=_parse_decimal_val(data.get("duty_amount")),
        igst_amount=_parse_decimal_val(data.get("igst_amount")),
        other_customs_charges=_parse_decimal_val(data.get("other_customs_charges")),
        total_customs_amount=_parse_decimal_val(data.get("total_customs_amount")),
        remark=data.get("remark"),
    )
    db.session.add(record)
    db.session.flush()
    return record


def update_customs_clearance(record: CustomsClearance, data: dict) -> CustomsClearance:
    if "project_id" in data:
        record.project_id = data["project_id"]
    if "bill_of_entry_id" in data:
        record.bill_of_entry_id = data["bill_of_entry_id"]
    if "cha_name" in data and data["cha_name"] is not None:
        record.cha_name = data["cha_name"]
    if "bill_of_entry_no" in data:
        record.bill_of_entry_no = data["bill_of_entry_no"]
    if "boe_date" in data:
        record.boe_date = _parse_date_val(data["boe_date"])
    if "customs_location" in data:
        record.customs_location = data["customs_location"]
    if "duty_paid_date" in data:
        record.duty_paid_date = _parse_date_val(data["duty_paid_date"])
    if "challan_no" in data:
        record.challan_no = data["challan_no"]
    if "cfs_name" in data:
        record.cfs_name = data["cfs_name"]
    if "transaction_ref_no" in data:
        record.transaction_ref_no = data["transaction_ref_no"]
    if "duty_amount" in data:
        record.duty_amount = _parse_decimal_val(data["duty_amount"])
    if "igst_amount" in data:
        record.igst_amount = _parse_decimal_val(data["igst_amount"])
    if "other_customs_charges" in data:
        record.other_customs_charges = _parse_decimal_val(data["other_customs_charges"])
    if "total_customs_amount" in data:
        record.total_customs_amount = _parse_decimal_val(data["total_customs_amount"])
    if "remark" in data:
        record.remark = data["remark"]

    record.updated_at = datetime.utcnow()
    db.session.flush()
    return record


def delete_customs_clearance(record: CustomsClearance) -> None:
    db.session.delete(record)
    db.session.flush()
