from datetime import date, datetime
from decimal import Decimal
import re

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models.eway_bill import EWayBill, EWayBillItem
from app.utils.date_utils import parse_date_input
from app.utils.remark_utils import normalize_remark_for_db


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
    parsed = parse_date_input(s)
    if parsed is not None:
        return parsed
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s)
    except Exception:
        return None


def _parse_decimal_val(val) -> Decimal | None:
    if val is None:
        return None
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    s = str(val).strip()
    if not s:
        return None
    match = re.search(r"[-+]?(?:\d*\.\d+|\d+)", s)
    if not match:
        return None
    return Decimal(match.group(0))


def _normalize_optional_string(val) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _replace_items(eway_bill: EWayBill, items: list[dict]) -> None:
    eway_bill.items.clear()
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        sr = item.get("sr_no") or (idx + 1)
        mat_name = _normalize_optional_string(
            item.get("material_name") or item.get("description")
        )
        desc = _normalize_optional_string(
            item.get("description") or item.get("material_name")
        ) or ""
        hsn = _normalize_optional_string(
            item.get("hsn_sac") or item.get("hsn_code") or item.get("hsn")
        )
        qty = _parse_decimal_val(item.get("quantity"))
        unit_str = _normalize_optional_string(item.get("unit") or item.get("uom")) or "NOS"
        unit_price = _parse_decimal_val(item.get("unit_price"))
        tot_amt = _parse_decimal_val(
            item.get("total_amount")
            if item.get("total_amount") is not None
            else item.get("net_amount")
            if item.get("net_amount") is not None
            else item.get("amount")
            if item.get("amount") is not None
            else item.get("total_price")
        )
        if tot_amt is None and qty is not None and unit_price is not None:
            tot_amt = (qty * unit_price).quantize(Decimal("0.01"))

        ewb_item = EWayBillItem(
            sr_no=sr,
            material_name=mat_name,
            description=desc,
            hsn_sac=hsn,
            quantity=qty,
            unit=unit_str,
            unit_price=unit_price,
            total_amount=tot_amt,
        )
        eway_bill.items.append(ewb_item)


def create_eway_bill(*, data: dict) -> EWayBill:
    eway_bill = EWayBill(
        project_id=data["project_id"],
        eway_bill_no=_normalize_optional_string(data.get("eway_bill_no")),
        eway_bill_date=_parse_date_val(data.get("eway_bill_date")),
        valid_from=_parse_date_val(data.get("valid_from")),
        valid_until=_parse_date_val(data.get("valid_until")),
        document_no=_normalize_optional_string(data.get("document_no")),
        document_date=_parse_date_val(data.get("document_date")),
        value=_parse_decimal_val(data.get("value")),
        place_of_dispatch=_normalize_optional_string(data.get("place_of_dispatch")),
        place_of_delivery=_normalize_optional_string(data.get("place_of_delivery")),
        transporter=_normalize_optional_string(data.get("transporter")),
        mode=_normalize_optional_string(data.get("mode")),
        vehicle_trans_doc_no=_normalize_optional_string(data.get("vehicle_trans_doc_no")),
        status=data.get("status") or "completed",
        remark=normalize_remark_for_db(data.get("remark") if "remark" in data else data.get("remarks")),
    )

    if "items" in data and data["items"]:
        _replace_items(eway_bill, data["items"])

    db.session.add(eway_bill)
    db.session.flush()
    return eway_bill


def get_eway_bill(eway_bill_id: int) -> EWayBill | None:
    return db.session.execute(
        db.select(EWayBill)
        .options(selectinload(EWayBill.items))
        .where(EWayBill.id == eway_bill_id)
    ).scalar_one_or_none()


def list_eway_bills(
    *,
    project_id: int | None = None,
    eway_bill_no: str | None = None,
) -> list[EWayBill]:
    statement = db.select(EWayBill).options(selectinload(EWayBill.items))
    if project_id is not None:
        statement = statement.where(EWayBill.project_id == project_id)
    if eway_bill_no is not None:
        statement = statement.where(EWayBill.eway_bill_no.ilike(f"%{eway_bill_no}%"))
    return db.session.execute(statement.order_by(EWayBill.id.desc())).scalars().all()


def update_eway_bill(
    eway_bill: EWayBill,
    *,
    data: dict,
) -> EWayBill:
    if "project_id" in data and data["project_id"] is not None:
        eway_bill.project_id = data["project_id"]
    if "eway_bill_no" in data:
        eway_bill.eway_bill_no = _normalize_optional_string(data["eway_bill_no"])
    if "eway_bill_date" in data:
        eway_bill.eway_bill_date = _parse_date_val(data["eway_bill_date"])
    if "valid_from" in data:
        eway_bill.valid_from = _parse_date_val(data["valid_from"])
    if "valid_until" in data:
        eway_bill.valid_until = _parse_date_val(data["valid_until"])
    if "document_no" in data:
        eway_bill.document_no = _normalize_optional_string(data["document_no"])
    if "document_date" in data:
        eway_bill.document_date = _parse_date_val(data["document_date"])
    if "value" in data:
        eway_bill.value = _parse_decimal_val(data["value"])
    if "place_of_dispatch" in data:
        eway_bill.place_of_dispatch = _normalize_optional_string(data["place_of_dispatch"])
    if "place_of_delivery" in data:
        eway_bill.place_of_delivery = _normalize_optional_string(data["place_of_delivery"])
    if "transporter" in data:
        eway_bill.transporter = _normalize_optional_string(data["transporter"])
    if "mode" in data:
        eway_bill.mode = _normalize_optional_string(data["mode"])
    if "vehicle_trans_doc_no" in data:
        eway_bill.vehicle_trans_doc_no = _normalize_optional_string(data["vehicle_trans_doc_no"])
    if "status" in data and data["status"]:
        eway_bill.status = data["status"]
    if "remark" in data or "remarks" in data:
        eway_bill.remark = normalize_remark_for_db(data.get("remark") if "remark" in data else data.get("remarks"))

    if "items" in data and data["items"] is not None:
        _replace_items(eway_bill, data["items"])

    return eway_bill


def delete_eway_bill(eway_bill: EWayBill) -> None:
    db.session.delete(eway_bill)

