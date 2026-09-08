import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import (
    CustomerDeliveryPackingList,
    CustomerDeliveryPackingListItem,
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


def _parse_int_val(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _replace_items(
    packing_list: CustomerDeliveryPackingList,
    items: list[dict],
) -> None:
    packing_list.items.clear()
    for item in items:
        pkg_no = _normalize_optional_string(
            item.get("package_no") or item.get("packageNo")
        )
        mat_name = _normalize_optional_string(
            item.get("material_name") or item.get("material_description")
        ) or ""
        hsn = _normalize_optional_string(
            item.get("hsn_code") or item.get("hsn_sac")
        )
        qty = _parse_decimal_val(item.get("quantity"))
        if qty is None:
            qty = Decimal("1.000")

        weight = _parse_decimal_val(
            item.get("weight") or item.get("total_weight_kg") or item.get("weight_per_unit_kg")
        )

        item_obj = CustomerDeliveryPackingListItem(
            package_no=pkg_no,
            material_name=mat_name,
            hsn_code=hsn,
            quantity=qty,
            weight=weight,
        )
        packing_list.items.append(item_obj)


def create_customer_delivery_packing_list(*, data: dict) -> CustomerDeliveryPackingList:
    packing_list_date_val = _parse_date_val(data.get("packing_list_date"))

    packing_list = CustomerDeliveryPackingList(
        project_id=data["project_id"],
        packing_list_no=str(
            data.get("packing_list_no") or data.get("packing_list_number")
        ).strip(),
        packing_list_date=packing_list_date_val,
        total_no_of_packs=_parse_int_val(data.get("total_no_of_packs")),
        packing_condition=_normalize_optional_string(data.get("packing_condition")),
        net_weight=_normalize_optional_string(
            data.get("net_weight") or data.get("net_weight_kg")
        ),
        gross_weight=_normalize_optional_string(
            data.get("gross_weight") or data.get("gross_weight_kg")
        ),
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    items_data = data.get("items") or []
    _replace_items(packing_list, items_data)

    db.session.add(packing_list)
    return packing_list


def get_customer_delivery_packing_list(packing_list_id: int) -> CustomerDeliveryPackingList | None:
    return (
        CustomerDeliveryPackingList.query.options(
            selectinload(CustomerDeliveryPackingList.items)
        )
        .filter(CustomerDeliveryPackingList.id == packing_list_id)
        .first()
    )


def list_customer_delivery_packing_lists(
    *,
    project_id: int | None = None,
    packing_list_no: str | None = None,
) -> list[CustomerDeliveryPackingList]:
    query = CustomerDeliveryPackingList.query.options(
        selectinload(CustomerDeliveryPackingList.items)
    )
    if project_id is not None:
        query = query.filter(CustomerDeliveryPackingList.project_id == project_id)
    if packing_list_no:
        query = query.filter(
            CustomerDeliveryPackingList.packing_list_no.ilike(f"%{packing_list_no.strip()}%")
        )

    return query.order_by(CustomerDeliveryPackingList.id.desc()).all()


def update_customer_delivery_packing_list(
    *,
    packing_list: CustomerDeliveryPackingList,
    data: dict,
) -> CustomerDeliveryPackingList:
    if "project_id" in data:
        packing_list.project_id = data["project_id"]

    if "packing_list_no" in data or "packing_list_number" in data:
        packing_list.packing_list_no = str(
            data.get("packing_list_no") or data.get("packing_list_number")
        ).strip()

    if "packing_list_date" in data:
        dt = _parse_date_val(data.get("packing_list_date"))
        if dt is not None:
            packing_list.packing_list_date = dt

    if "total_no_of_packs" in data:
        packing_list.total_no_of_packs = _parse_int_val(data.get("total_no_of_packs"))

    if "packing_condition" in data:
        packing_list.packing_condition = _normalize_optional_string(
            data.get("packing_condition")
        )

    if "net_weight" in data or "net_weight_kg" in data:
        packing_list.net_weight = _normalize_optional_string(
            data.get("net_weight") or data.get("net_weight_kg")
        )

    if "gross_weight" in data or "gross_weight_kg" in data:
        packing_list.gross_weight = _normalize_optional_string(
            data.get("gross_weight") or data.get("gross_weight_kg")
        )

    if "remark" in data or "remarks" in data:
        packing_list.remark = _normalize_optional_string(
            data.get("remark") or data.get("remarks")
        )

    if "items" in data and data["items"] is not None:
        _replace_items(packing_list, data["items"])

    packing_list.updated_at = datetime.utcnow()
    return packing_list


def delete_customer_delivery_packing_list(packing_list_id: int) -> list[str]:
    packing_list = get_customer_delivery_packing_list(packing_list_id)
    if packing_list is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type="customer_delivery_packing_list",
        entity_id=packing_list_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(packing_list)
    return storage_keys

