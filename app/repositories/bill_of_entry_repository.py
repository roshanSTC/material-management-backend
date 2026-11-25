from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

from app.extensions.database import db
from app.models import BillOfEntry, Project
from app.utils.remark_utils import normalize_remark_for_db


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
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s[:10])
    except Exception:
        return None


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
    boe_filing_date = _parse_date_val(data.get("boe_filing_date"))
    record = BillOfEntry(
        project_id=data["project_id"],
        logistic_mode=data.get("logistic_mode"),
        shipment_date=_parse_date_val(data.get("shipment_date")),
        awb_bl_no=data.get("awb_bl_no"),
        flight_vessel_name=data.get("flight_vessel_name"),
        flight_vessel_no=data.get("flight_vessel_no"),
        port_loading=data.get("port_loading"),
        port_discharge=data.get("port_discharge"),
        bill_of_entry_no=data.get("bill_of_entry_no"),
        boe_filing_date=boe_filing_date,
        total_assessable_value=_parse_decimal_val(data.get("total_assessable_value")),
        basic_custom_duty_bcd=_parse_decimal_val(data.get("basic_custom_duty_bcd")),
        sws=_parse_decimal_val(data.get("sws")),
        igst=_parse_decimal_val(data.get("igst")),
        duty_paid_date=_parse_date_val(data.get("duty_paid_date")),
        challan_no=data.get("challan_no"),
        payment_ref_no=data.get("payment_ref_no"),
        customs_location=data.get("customs_location"),
        cfs_name=data.get("cfs_name"),
        total_duty=_parse_decimal_val(data.get("total_duty")),
        remark=normalize_remark_for_db(data.get("remark")),
    )
    db.session.add(record)
    db.session.flush()
    return record


def update_bill_of_entry(record: BillOfEntry, data: dict) -> BillOfEntry:
    if "project_id" in data:
        record.project_id = data["project_id"]
    for str_field in (
        "logistic_mode",
        "awb_bl_no",
        "flight_vessel_name",
        "flight_vessel_no",
        "port_loading",
        "port_discharge",
        "bill_of_entry_no",
        "challan_no",
        "payment_ref_no",
        "customs_location",
        "cfs_name",
    ):
        if str_field in data:
            setattr(record, str_field, data[str_field])
    for dt_field in ("shipment_date", "boe_filing_date", "duty_paid_date"):
        if dt_field in data:
            setattr(record, dt_field, _parse_date_val(data[dt_field]))
    for dec_field in ("total_assessable_value", "basic_custom_duty_bcd", "sws", "igst", "total_duty"):
        if dec_field in data:
            setattr(record, dec_field, _parse_decimal_val(data[dec_field]))
    if "remark" in data:
        record.remark = normalize_remark_for_db(data["remark"])

    record.updated_at = datetime.utcnow()
    db.session.flush()
    return record


def delete_bill_of_entry(record: BillOfEntry) -> None:
    db.session.delete(record)
    db.session.flush()

