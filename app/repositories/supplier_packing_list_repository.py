import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import (
    Project,
    Supplier,
    SupplierPackingList,
    SupplierPackingListItem,
)


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


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
    packing_list: SupplierPackingList,
    items: list[dict],
) -> None:
    packing_list.items.clear()
    for item in items:
        mat_name = _normalize_optional_string(
            item.get("material_name") or item.get("description")
        )
        desc = _normalize_optional_string(
            item.get("description") or item.get("material_name")
        ) or ""
        hsn = _normalize_optional_string(
            item.get("hsn_code") or item.get("hsn_sac") or item.get("hsn")
        )
        qty = _parse_decimal_val(item.get("quantity")) or Decimal("1")
        unit_price = _parse_decimal_val(item.get("unit_price"))
        if unit_price is None:
            unit_price = Decimal("0.00")

        net_amt = _parse_decimal_val(item.get("net_amount"))
        if net_amt is None and unit_price is not None and qty is not None:
            net_amt = (qty * unit_price).quantize(Decimal("0.01"))

        unit_weight = _parse_decimal_val(
            item.get("unit_weight")
            if item.get("unit_weight") is not None
            else item.get("unit_weight_kg")
            if item.get("unit_weight_kg") is not None
            else item.get("weight")
        )
        weight = _parse_decimal_val(item.get("weight"))
        if weight is None:
            weight = unit_weight

        total_weight = _parse_decimal_val(item.get("total_weight"))
        if total_weight is None and unit_weight is not None and qty is not None:
            total_weight = (qty * unit_weight).quantize(Decimal("0.001"))

        item_obj = SupplierPackingListItem(
            material_name=mat_name,
            description=desc,
            hsn_code=hsn,
            quantity=qty,
            unit_price=unit_price,
            net_amount=net_amt,
            weight=weight,
            unit_weight=unit_weight,
            total_weight=total_weight,
        )
        packing_list.items.append(item_obj)


def create_supplier_packing_list(*, data: dict) -> SupplierPackingList:
    packing_date_val = _parse_date_val(
        data.get("packing_list_date")
    )

    tot_weight = _parse_decimal_val(
        data.get("total_weight")
        if data.get("total_weight") is not None
        else data.get("total_gross_weight_kg")
        if data.get("total_gross_weight_kg") is not None
        else data.get("weight")
    )
    weight = _parse_decimal_val(data.get("weight"))
    if weight is None:
        weight = tot_weight

    packing_list = SupplierPackingList(
        project_id=data["project_id"],
        supplier_id=data["supplier_id"],
        packing_list_no=str(
            data.get("packing_list_no") or data.get("packing_list_number")
        ).strip(),
        packing_list_date=packing_date_val,
        packing_condition=_normalize_optional_string(data.get("packing_condition")),
        weight=weight,
        total_weight=tot_weight,
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    items_data = data.get("items") or []
    _replace_items(packing_list, items_data)

    db.session.add(packing_list)
    return packing_list


def get_supplier_packing_list(packing_list_id: int) -> SupplierPackingList | None:
    return (
        SupplierPackingList.query.options(selectinload(SupplierPackingList.items))
        .filter(SupplierPackingList.id == packing_list_id)
        .first()
    )


def get_supplier_packing_list_by_project(project_id: int) -> SupplierPackingList | None:
    return (
        SupplierPackingList.query.options(selectinload(SupplierPackingList.items))
        .filter(SupplierPackingList.project_id == project_id)
        .order_by(SupplierPackingList.id.desc())
        .first()
    )


def list_supplier_packing_lists(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
    packing_list_no: str | None = None,
) -> list[SupplierPackingList]:
    query = SupplierPackingList.query.options(
        selectinload(SupplierPackingList.items)
    )
    if project_id is not None:
        query = query.filter(SupplierPackingList.project_id == project_id)
    if supplier_id is not None:
        query = query.filter(SupplierPackingList.supplier_id == supplier_id)
    if packing_list_no:
        query = query.filter(
            SupplierPackingList.packing_list_no.ilike(f"%{packing_list_no.strip()}%")
        )

    return query.order_by(SupplierPackingList.id.desc()).all()


def update_supplier_packing_list(
    *,
    packing_list: SupplierPackingList,
    data: dict,
) -> SupplierPackingList:
    if "project_id" in data:
        packing_list.project_id = data["project_id"]
    if "supplier_id" in data:
        packing_list.supplier_id = data["supplier_id"]

    if "packing_list_no" in data or "packing_list_number" in data:
        packing_list.packing_list_no = str(
            data.get("packing_list_no") or data.get("packing_list_number")
        ).strip()

    if "packing_list_date" in data:
        dt = _parse_date_val(data.get("packing_list_date"))
        if dt is not None:
            packing_list.packing_list_date = dt

    if "packing_condition" in data:
        packing_list.packing_condition = _normalize_optional_string(data.get("packing_condition"))

    if "weight" in data:
        packing_list.weight = _parse_decimal_val(data.get("weight"))

    if "total_weight" in data or "total_gross_weight_kg" in data:
        packing_list.total_weight = _parse_decimal_val(
            data.get("total_weight")
            if data.get("total_weight") is not None
            else data.get("total_gross_weight_kg")
        )

    if "remark" in data or "remarks" in data:
        packing_list.remark = _normalize_optional_string(data.get("remark") or data.get("remarks"))

    if "items" in data and data["items"] is not None:
        _replace_items(packing_list, data["items"])

    packing_list.updated_at = datetime.utcnow()
    return packing_list


def delete_supplier_packing_list(packing_list_id: int) -> list[str]:
    packing_list = get_supplier_packing_list(packing_list_id)
    if packing_list is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type="supplier_packing_list",
        entity_id=packing_list_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(packing_list)
    return storage_keys

