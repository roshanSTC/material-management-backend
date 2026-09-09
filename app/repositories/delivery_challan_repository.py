import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import (
    DeliveryChallan,
    DeliveryChallanItem,
    Project,
)


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


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
    return date.fromisoformat(s)


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


def _replace_items(
    delivery_challan: DeliveryChallan,
    items: list[dict],
) -> None:
    delivery_challan.items.clear()
    for item in items:
        mat_name = _normalize_optional_string(
            item.get("material_name") or item.get("material_description")
        ) or ""
        hsn = _normalize_optional_string(
            item.get("hsn_code") or item.get("hsn_sac")
        )
        qty = _parse_decimal_val(item.get("quantity"))
        if qty is None:
            qty = Decimal("1.000")

        unit_price = _parse_decimal_val(
            item.get("unit_price") or item.get("rate_per_unit")
        )
        if unit_price is None:
            unit_price = Decimal("0.00")

        net_amt = _parse_decimal_val(
            item.get("net_amount") or item.get("amount")
        )
        if net_amt is None and unit_price is not None and qty is not None:
            net_amt = (qty * unit_price).quantize(Decimal("0.01"))
        elif net_amt is None:
            net_amt = Decimal("0.00")

        item_obj = DeliveryChallanItem(
            material_name=mat_name,
            hsn_code=hsn,
            quantity=qty,
            unit_price=unit_price,
            net_amount=net_amt,
        )
        delivery_challan.items.append(item_obj)


def create_delivery_challan(*, data: dict) -> DeliveryChallan:
    delivery_challan_date_val = _parse_date_val(data.get("delivery_challan_date"))

    delivery_challan = DeliveryChallan(
        project_id=data["project_id"],
        delivery_challan_no=str(
            data.get("delivery_challan_no") or data.get("delivery_challan_number")
        ).strip(),
        delivery_challan_date=delivery_challan_date_val,
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    items_data = data.get("items") or []
    _replace_items(delivery_challan, items_data)

    db.session.add(delivery_challan)
    return delivery_challan


def get_delivery_challan(delivery_challan_id: int) -> DeliveryChallan | None:
    return (
        DeliveryChallan.query.options(
            selectinload(DeliveryChallan.items)
        )
        .filter(DeliveryChallan.id == delivery_challan_id)
        .first()
    )


def list_delivery_challans(
    *,
    project_id: int | None = None,
    delivery_challan_no: str | None = None,
) -> list[DeliveryChallan]:
    query = DeliveryChallan.query.options(
        selectinload(DeliveryChallan.items)
    )
    if project_id is not None:
        query = query.filter(DeliveryChallan.project_id == project_id)
    if delivery_challan_no:
        query = query.filter(
            DeliveryChallan.delivery_challan_no.ilike(f"%{delivery_challan_no.strip()}%")
        )

    return query.order_by(DeliveryChallan.id.desc()).all()


def update_delivery_challan(
    *,
    delivery_challan: DeliveryChallan,
    data: dict,
) -> DeliveryChallan:
    if "project_id" in data:
        delivery_challan.project_id = data["project_id"]

    if "delivery_challan_no" in data or "delivery_challan_number" in data:
        delivery_challan.delivery_challan_no = str(
            data.get("delivery_challan_no") or data.get("delivery_challan_number")
        ).strip()

    if "delivery_challan_date" in data:
        dt = _parse_date_val(data.get("delivery_challan_date"))
        if dt is not None:
            delivery_challan.delivery_challan_date = dt

    if "remark" in data or "remarks" in data:
        delivery_challan.remark = _normalize_optional_string(
            data.get("remark") or data.get("remarks")
        )

    if "items" in data and data["items"] is not None:
        _replace_items(delivery_challan, data["items"])

    delivery_challan.updated_at = datetime.utcnow()
    return delivery_challan


def delete_delivery_challan(delivery_challan_id: int) -> list[str]:
    delivery_challan = get_delivery_challan(delivery_challan_id)
    if delivery_challan is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type="delivery_challan",
        entity_id=delivery_challan_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(delivery_challan)
    return storage_keys

