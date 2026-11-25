from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import CustomsClearance, CustomsClearanceItem, Project
from app.utils.remark_utils import normalize_remark_for_db


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_customs_clearance(clearance_id: int) -> CustomsClearance | None:
    return db.session.execute(
        select(CustomsClearance)
        .options(selectinload(CustomsClearance.items))
        .where(CustomsClearance.id == clearance_id)
    ).scalar_one_or_none()


def get_customs_clearance_by_project_id(project_id: int) -> CustomsClearance | None:
    stmt = (
        select(CustomsClearance)
        .options(selectinload(CustomsClearance.items))
        .where(CustomsClearance.project_id == project_id)
        .order_by(CustomsClearance.id.desc())
    )
    return db.session.execute(stmt).scalars().first()


def list_customs_clearances(
    project_id: int | None = None,
    invoice_no: str | None = None,
) -> list[CustomsClearance]:
    stmt = select(CustomsClearance).options(selectinload(CustomsClearance.items)).order_by(CustomsClearance.id.desc())

    if project_id is not None:
        stmt = stmt.where(CustomsClearance.project_id == project_id)
    if invoice_no is not None:
        stmt = stmt.where(CustomsClearance.invoice_no == invoice_no)

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


def _replace_items(record: CustomsClearance, items: list[dict]) -> None:
    record.items.clear()
    for idx, item in enumerate(items, start=1):
        record.items.append(
            CustomsClearanceItem(
                sr_no=item.get("sr_no") if item.get("sr_no") is not None else idx,
                description=str(item.get("description") or "").strip(),
                amount=_parse_decimal_val(item.get("amount")),
            )
        )


def create_customs_clearance(data: dict) -> CustomsClearance:
    record = CustomsClearance(
        project_id=data["project_id"],
        bill_of_entry_id=data.get("bill_of_entry_id"),
        freight_forwarder_name=data.get("freight_forwarder_name"),
        cha_name=data.get("cha_name"),
        invoice_no=data.get("invoice_no"),
        invoice_date=_parse_date_val(data.get("invoice_date")),
        invoice_amount=_parse_decimal_val(data.get("invoice_amount")),
        payment_date=_parse_date_val(data.get("payment_date")),
        payment_amount=_parse_decimal_val(data.get("payment_amount")),
        remark=normalize_remark_for_db(data.get("remark")),
    )
    if data.get("items"):
        _replace_items(record, data["items"])
    db.session.add(record)
    db.session.flush()
    return record


def update_customs_clearance(record: CustomsClearance, data: dict) -> CustomsClearance:
    if "project_id" in data:
        record.project_id = data["project_id"]
    if "bill_of_entry_id" in data:
        record.bill_of_entry_id = data["bill_of_entry_id"]
    for str_field in ("freight_forwarder_name", "cha_name", "invoice_no"):
        if str_field in data:
            setattr(record, str_field, data[str_field])
    for dt_field in ("invoice_date", "payment_date"):
        if dt_field in data:
            setattr(record, dt_field, _parse_date_val(data[dt_field]))
    for dec_field in ("invoice_amount", "payment_amount"):
        if dec_field in data:
            setattr(record, dec_field, _parse_decimal_val(data[dec_field]))
    if "remark" in data:
        record.remark = normalize_remark_for_db(data["remark"])
    if "items" in data and data["items"] is not None:
        _replace_items(record, data["items"])

    record.updated_at = datetime.utcnow()
    db.session.flush()
    return record


def delete_customs_clearance(record: CustomsClearance) -> None:
    db.session.delete(record)
    db.session.flush()
