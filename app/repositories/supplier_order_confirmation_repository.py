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
    order_confirmation: SupplierOrderConfirmation,
    items: list[dict],
) -> None:
    order_confirmation.items.clear()
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

        item_obj = SupplierOrderConfirmationItem(
            material_name=mat_name,
            description=desc,
            hsn_code=hsn,
            quantity=qty,
            unit_price=unit_price,
            net_amount=net_amt,
        )
        order_confirmation.items.append(item_obj)


def create_supplier_order_confirmation(*, data: dict) -> SupplierOrderConfirmation:
    conf_date = _parse_date_val(
        data.get("order_confirmation_date") or data.get("confirmation_date")
    ) or date.today()

    ref_num = _normalize_optional_string(
        data.get("ref_no") or data.get("reference_number")
    )
    ship_terms = _normalize_optional_string(
        data.get("shipping_terms") or data.get("shipping_term")
    )
    del_period = _normalize_optional_string(
        data.get("delivery_period") or data.get("delivery_term")
    )
    pay_terms = _normalize_optional_string(
        data.get("payment_terms") or data.get("payment_term")
    )
    remarks = _normalize_optional_string(
        data.get("remark") or data.get("remarks")
    )

    confirmation = SupplierOrderConfirmation(
        project_id=data["project_id"],
        supplier_id=data.get("supplier_id"),
        purchase_order_id=data.get("purchase_order_id") or data.get("po_id"),
        order_confirmation_date=conf_date,
        email=_normalize_optional_string(data.get("email")),
        ref_no=ref_num,
        shipping_terms=ship_terms,
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
        delivery_period=del_period,
        payment_terms=pay_terms,
        total_amount=_parse_decimal_val(data.get("total_amount")),
        total_net_amount=_parse_decimal_val(data.get("total_net_amount")),
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
    ref_no: str | None = None,
) -> list[SupplierOrderConfirmation]:
    statement = db.select(SupplierOrderConfirmation).options(
        selectinload(SupplierOrderConfirmation.items)
    )
    if project_id is not None:
        statement = statement.where(SupplierOrderConfirmation.project_id == project_id)
    if supplier_id is not None:
        statement = statement.where(SupplierOrderConfirmation.supplier_id == supplier_id)
    if ref_no is not None:
        statement = statement.where(
            SupplierOrderConfirmation.ref_no.ilike(f"%{ref_no}%")
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
    if "purchase_order_id" in data or "po_id" in data:
        confirmation.purchase_order_id = data.get("purchase_order_id") or data.get("po_id")
    if "order_confirmation_date" in data or "confirmation_date" in data:
        conf_date = _parse_date_val(
            data.get("order_confirmation_date") or data.get("confirmation_date")
        )
        if conf_date is not None:
            confirmation.order_confirmation_date = conf_date
    if "email" in data:
        confirmation.email = _normalize_optional_string(data["email"])
    if "ref_no" in data or "reference_number" in data:
        confirmation.ref_no = _normalize_optional_string(
            data.get("ref_no") or data.get("reference_number")
        )
    if "shipping_terms" in data or "shipping_term" in data:
        confirmation.shipping_terms = _normalize_optional_string(
            data.get("shipping_terms") or data.get("shipping_term")
        )
    if "warranty_period" in data:
        confirmation.warranty_period = _normalize_optional_string(data["warranty_period"])
    if "delivery_period" in data or "delivery_term" in data:
        confirmation.delivery_period = _normalize_optional_string(
            data.get("delivery_period") or data.get("delivery_term")
        )
    if "payment_terms" in data or "payment_term" in data:
        confirmation.payment_terms = _normalize_optional_string(
            data.get("payment_terms") or data.get("payment_term")
        )
    if "total_amount" in data:
        confirmation.total_amount = _parse_decimal_val(data["total_amount"])
    if "total_net_amount" in data:
        confirmation.total_net_amount = _parse_decimal_val(data["total_net_amount"])
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

