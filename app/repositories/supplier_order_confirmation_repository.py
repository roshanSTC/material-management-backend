import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import (
    Project,
    PurchaseOrder,
    Supplier,
    SupplierOrderConfirmation,
    SupplierOrderConfirmationItem,
)


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


def get_purchase_order(purchase_order_id: int) -> PurchaseOrder | None:
    return db.session.get(PurchaseOrder, purchase_order_id)


from app.utils.remark_utils import normalize_remark_for_db


def _normalize_optional_string(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return normalize_remark_for_db(value)
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
    order_confirmation: SupplierOrderConfirmation,
    items: list[dict],
) -> None:
    order_confirmation.items.clear()
    for idx, item in enumerate(items, start=1):
        desc = _normalize_optional_string(item.get("description")) or ""
        hsn = _normalize_optional_string(item.get("hsn_sac"))
        qty = _parse_decimal_val(item.get("quantity")) or Decimal("1")
        unit_price = _parse_decimal_val(item.get("unit_price"))
        if unit_price is None:
            unit_price = Decimal("0.00")

        total_amt = _parse_decimal_val(item.get("total_amount"))
        if total_amt is None and unit_price is not None and qty is not None:
            total_amt = (qty * unit_price).quantize(Decimal("0.01"))

        item_obj = SupplierOrderConfirmationItem(
            sr_no=item.get("sr_no") if item.get("sr_no") is not None else idx,
            description=desc,
            hsn_sac=hsn,
            quantity=qty,
            unit_price=unit_price,
            total_amount=total_amt,
        )
        order_confirmation.items.append(item_obj)


def create_supplier_order_confirmation(*, data: dict) -> SupplierOrderConfirmation:
    conf_date = _parse_date_val(data.get("order_confirmation_date")) or date.today()

    oc_no = _normalize_optional_string(data.get("order_confirmation_no")) or ""
    incoterms_val = _normalize_optional_string(data.get("incoterms"))
    del_period = _normalize_optional_string(data.get("delivery_period"))
    pay_terms = _normalize_optional_string(data.get("payment_terms"))
    remarks = _normalize_optional_string(
        data.get("remark") or data.get("remarks")
    )

    curr_unit = _normalize_optional_string(
        data.get("currency_unit") or data.get("currency")
    )

    confirmation = SupplierOrderConfirmation(
        project_id=data["project_id"],
        supplier_id=data.get("supplier_id"),
        supplier_name=_normalize_optional_string(data.get("supplier_name")),
        purchase_order_id=data.get("purchase_order_id"),
        order_confirmation_date=conf_date,
        email=_normalize_optional_string(data.get("email")),
        order_confirmation_no=oc_no,
        incoterms=incoterms_val,
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
        delivery_period=del_period,
        payment_terms=pay_terms,
        total_amount=_parse_decimal_val(data.get("total_amount")),
        total_net_amount=_parse_decimal_val(data.get("total_net_amount")),
        currency_unit=curr_unit.upper() if curr_unit else None,
        remark=remarks,
    )

    if "items" in data and data["items"]:
        _replace_items(confirmation, data["items"])

    db.session.add(confirmation)
    db.session.flush()
    return confirmation


def get_supplier_order_confirmation(order_confirmation_id: int) -> SupplierOrderConfirmation | None:
    return db.session.execute(
        db.select(SupplierOrderConfirmation)
        .options(selectinload(SupplierOrderConfirmation.items))
        .where(SupplierOrderConfirmation.id == order_confirmation_id)
    ).scalar_one_or_none()


def get_supplier_order_confirmation_by_project(project_id: int) -> SupplierOrderConfirmation | None:
    return db.session.execute(
        db.select(SupplierOrderConfirmation)
        .options(selectinload(SupplierOrderConfirmation.items))
        .where(SupplierOrderConfirmation.project_id == project_id)
        .order_by(SupplierOrderConfirmation.id.desc())
    ).scalars().first()


def list_supplier_order_confirmations(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
    order_confirmation_no: str | None = None,
) -> list[SupplierOrderConfirmation]:
    statement = db.select(SupplierOrderConfirmation).options(
        selectinload(SupplierOrderConfirmation.items)
    )
    if project_id is not None:
        statement = statement.where(SupplierOrderConfirmation.project_id == project_id)
    if supplier_id is not None:
        statement = statement.where(SupplierOrderConfirmation.supplier_id == supplier_id)
    if order_confirmation_no is not None:
        statement = statement.where(
            SupplierOrderConfirmation.order_confirmation_no.ilike(f"%{order_confirmation_no}%")
        )

    return db.session.execute(
        statement.order_by(SupplierOrderConfirmation.id.desc())
    ).scalars().all()


def update_supplier_order_confirmation(
    confirmation: SupplierOrderConfirmation,
    *,
    data: dict,
) -> SupplierOrderConfirmation:
    if "project_id" in data:
        confirmation.project_id = data["project_id"]
    if "supplier_id" in data:
        confirmation.supplier_id = data["supplier_id"]
    if "supplier_name" in data:
        confirmation.supplier_name = _normalize_optional_string(data["supplier_name"])
    if "purchase_order_id" in data:
        confirmation.purchase_order_id = data["purchase_order_id"]
    if "order_confirmation_date" in data:
        conf_date = _parse_date_val(data["order_confirmation_date"])
        if conf_date is not None:
            confirmation.order_confirmation_date = conf_date
    if "email" in data:
        confirmation.email = _normalize_optional_string(data["email"])
    if "order_confirmation_no" in data:
        confirmation.order_confirmation_no = _normalize_optional_string(data["order_confirmation_no"]) or confirmation.order_confirmation_no
    if "incoterms" in data:
        confirmation.incoterms = _normalize_optional_string(data["incoterms"])
    if "warranty_period" in data:
        confirmation.warranty_period = _normalize_optional_string(data["warranty_period"])
    if "delivery_period" in data:
        confirmation.delivery_period = _normalize_optional_string(data["delivery_period"])
    if "payment_terms" in data:
        confirmation.payment_terms = _normalize_optional_string(data["payment_terms"])
    if "total_amount" in data:
        confirmation.total_amount = _parse_decimal_val(data["total_amount"])
    if "total_net_amount" in data:
        confirmation.total_net_amount = _parse_decimal_val(data["total_net_amount"])
    if "currency_unit" in data or "currency" in data:
        curr_unit = _normalize_optional_string(
            data.get("currency_unit") or data.get("currency")
        )
        confirmation.currency_unit = curr_unit.upper() if curr_unit else None
    if "remark" in data or "remarks" in data:
        confirmation.remark = _normalize_optional_string(
            data.get("remark") or data.get("remarks")
        )

    if "items" in data and data["items"] is not None:
        _replace_items(confirmation, data["items"])

    return confirmation


def delete_supplier_order_confirmation(
    confirmation: SupplierOrderConfirmation,
) -> None:
    db.session.delete(confirmation)

