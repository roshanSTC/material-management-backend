import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import Customer, CustomerTender, Project, PurchaseOrder, PurchaseOrderItem


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_customer(customer_id: int) -> Customer | None:
    return db.session.get(Customer, customer_id)


def get_customer_tender(tender_id: int) -> CustomerTender | None:
    return db.session.get(CustomerTender, tender_id)


from app.utils.remark_utils import normalize_remark_for_db


def _normalize_optional_string(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return normalize_remark_for_db(value)
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _parse_date_val(val) -> date | None:
    if val is None or val == "":
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    try:
        from app.utils.date_utils import parse_date_input
        return parse_date_input(s)
    except Exception:
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


def _replace_items(purchase_order: PurchaseOrder, items: list[dict]) -> None:
    purchase_order.items.clear()
    for item in items:
        mat_name = _normalize_optional_string(
            item.get("material_name") or item.get("description")
        )
        desc = _normalize_optional_string(
            item.get("description") or item.get("material_name")
        ) or ""
        hsn = _normalize_optional_string(
            item.get("hsn_code") or item.get("hsn_sac")
        )
        qty = _parse_decimal_val(item.get("quantity")) or Decimal("1")
        unit_price = _parse_decimal_val(item.get("unit_price"))
        if unit_price is None:
            unit_price = Decimal("0.00")

        net_amt = _parse_decimal_val(item.get("net_amount"))
        if net_amt is None:
            net_amt = _parse_decimal_val(item.get("total_price"))
        if net_amt is None and unit_price is not None and qty is not None:
            net_amt = (qty * unit_price).quantize(Decimal("0.01"))

        unit_str = _normalize_optional_string(item.get("unit")) or "NOS"
        item_delivery_date = _parse_date_val(item.get("delivery_date") or item.get("deliveryDate")) or purchase_order.delivery_date

        po_item = PurchaseOrderItem(
            material_name=mat_name,
            description=desc,
            hsn_code=hsn,
            quantity=qty,
            unit_price=unit_price,
            net_amount=net_amt,
            unit=unit_str,
            delivery_date=item_delivery_date,
        )
        purchase_order.items.append(po_item)


def create_purchase_order(*, data: dict) -> PurchaseOrder:
    po_num = str(
        data.get("po_no")
        if data.get("po_no") is not None
        else data.get("po_number", "")
    ).strip()

    gst_val = (
        data.get("gst_rate_pct")
        if data.get("gst_rate_pct") is not None
        else data.get("gst_pct")
        if data.get("gst_pct") is not None
        else data.get("gst_rate")
        if data.get("gst_rate") is not None
        else data.get("gst")
    )
    gst_rate_val = _parse_decimal_val(gst_val)

    del_date_val = _parse_date_val(data.get("delivery_date") or data.get("deliveryDate"))
    if del_date_val is None and data.get("items"):
        for it in data["items"]:
            if isinstance(it, dict):
                parsed = _parse_date_val(it.get("delivery_date") or it.get("deliveryDate"))
                if parsed:
                    del_date_val = parsed
                    break

    net_amt_val = _parse_decimal_val(data.get("total_net_amount"))
    if net_amt_val is None and data.get("items"):
        tot = Decimal("0.00")
        for it in data["items"]:
            if isinstance(it, dict):
                it_qty = _parse_decimal_val(it.get("quantity")) or Decimal("1")
                it_price = _parse_decimal_val(it.get("unit_price")) or Decimal("0.00")
                it_net = _parse_decimal_val(it.get("net_amount")) or _parse_decimal_val(it.get("total_price")) or (it_qty * it_price)
                tot += it_net
        net_amt_val = tot.quantize(Decimal("0.01"))

    gst_amt_val = _parse_decimal_val(data.get("gst_amount"))
    if gst_amt_val is None and gst_rate_val is not None and net_amt_val is not None:
        gst_amt_val = (net_amt_val * gst_rate_val / Decimal("100")).quantize(Decimal("0.01"))

    gross_amt_val = _parse_decimal_val(data.get("total_gross_amount"))
    if gross_amt_val is None and net_amt_val is not None:
        gross_amt_val = (net_amt_val + (gst_amt_val or Decimal("0.00"))).quantize(Decimal("0.01"))

    purchase_order = PurchaseOrder(
        project_id=data["project_id"],
        customer_id=data.get("customer_id"),
        tender_id=data.get("tender_id"),
        po_title=_normalize_optional_string(data.get("po_title")) or "",
        po_number=po_num,
        poc_name=_normalize_optional_string(data.get("poc_name")),
        email=_normalize_optional_string(data.get("email")),
        contact=_normalize_optional_string(data.get("contact")),
        po_date=_parse_date_val(data.get("po_date") or data.get("poDate")),
        delivery_date=del_date_val,
        delivery_term=_normalize_optional_string(
            data.get("delivery_term") or data.get("delivery_terms")
        ),
        payment_terms=_normalize_optional_string(
            data.get("payment_terms") or data.get("payment_term")
        ),
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
        gst_rate=gst_rate_val,
        gst_amount=gst_amt_val,
        total_net_amount=net_amt_val,
        total_gross_amount=gross_amt_val,
        remark=normalize_remark_for_db(
            data.get("remark") if data.get("remark") is not None else data.get("remarks")
        ),
    )

    if "items" in data and data["items"]:
        _replace_items(purchase_order, data["items"])

    db.session.add(purchase_order)
    db.session.flush()
    return purchase_order


def get_purchase_order(purchase_order_id: int) -> PurchaseOrder | None:
    return db.session.execute(
        db.select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.id == purchase_order_id)
    ).scalar_one_or_none()


def list_purchase_orders(
    *,
    project_id: int | None = None,
    customer_id: int | None = None,
    po_number: str | None = None,
) -> list[PurchaseOrder]:
    statement = db.select(PurchaseOrder).options(
        selectinload(PurchaseOrder.items)
    )
    if project_id is not None:
        statement = statement.where(PurchaseOrder.project_id == project_id)
    if customer_id is not None:
        statement = statement.where(PurchaseOrder.customer_id == customer_id)
    if po_number is not None:
        statement = statement.where(PurchaseOrder.po_number.ilike(f"%{po_number}%"))

    return db.session.execute(
        statement.order_by(PurchaseOrder.id.desc())
    ).scalars().all()


def get_latest_purchase_order_for_project(project_id: int) -> PurchaseOrder | None:
    return db.session.execute(
        db.select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.items))
        .where(PurchaseOrder.project_id == project_id)
        .order_by(PurchaseOrder.id.desc())
    ).scalars().first()


def update_purchase_order(
    purchase_order: PurchaseOrder,
    *,
    data: dict,
) -> PurchaseOrder:
    if "project_id" in data:
        purchase_order.project_id = data["project_id"]
    if "customer_id" in data:
        purchase_order.customer_id = data["customer_id"]
    if "tender_id" in data:
        purchase_order.tender_id = data["tender_id"]
    if "po_title" in data and data["po_title"] is not None:
        purchase_order.po_title = _normalize_optional_string(data["po_title"]) or ""
    if "po_no" in data or "po_number" in data:
        po_num = data.get("po_no") if data.get("po_no") is not None else data.get("po_number")
        if po_num is not None:
            purchase_order.po_number = str(po_num).strip()
    if "poc_name" in data:
        purchase_order.poc_name = _normalize_optional_string(data["poc_name"])
    if "email" in data:
        purchase_order.email = _normalize_optional_string(data["email"])
    if "contact" in data:
        purchase_order.contact = _normalize_optional_string(data["contact"])
    if "po_date" in data:
        purchase_order.po_date = _parse_date_val(data.get("po_date") or data.get("poDate"))
    if "delivery_date" in data or "deliveryDate" in data:
        del_date_val = _parse_date_val(data.get("delivery_date") or data.get("deliveryDate"))
        if del_date_val is not None:
            purchase_order.delivery_date = del_date_val
    elif purchase_order.delivery_date is None and data.get("items"):
        for it in data["items"]:
            if isinstance(it, dict):
                parsed = _parse_date_val(it.get("delivery_date") or it.get("deliveryDate"))
                if parsed:
                    purchase_order.delivery_date = parsed
                    break

    if "delivery_term" in data or "delivery_terms" in data:
        purchase_order.delivery_term = _normalize_optional_string(
            data.get("delivery_term") or data.get("delivery_terms")
        )
    if "payment_terms" in data or "payment_term" in data:
        purchase_order.payment_terms = _normalize_optional_string(
            data.get("payment_terms") or data.get("payment_term")
        )
    if "warranty_period" in data:
        purchase_order.warranty_period = _normalize_optional_string(data["warranty_period"])

    if (
        "gst_rate" in data
        or "gst" in data
        or "gst_rate_pct" in data
        or "gst_pct" in data
    ):
        gst_val = (
            data.get("gst_rate_pct")
            if data.get("gst_rate_pct") is not None
            else data.get("gst_pct")
            if data.get("gst_pct") is not None
            else data.get("gst_rate")
            if data.get("gst_rate") is not None
            else data.get("gst")
        )
        purchase_order.gst_rate = _parse_decimal_val(gst_val)

    if "total_net_amount" in data and data["total_net_amount"] is not None:
        purchase_order.total_net_amount = _parse_decimal_val(data["total_net_amount"])
    elif purchase_order.total_net_amount is None and data.get("items"):
        tot = Decimal("0.00")
        for it in data["items"]:
            if isinstance(it, dict):
                it_qty = _parse_decimal_val(it.get("quantity")) or Decimal("1")
                it_price = _parse_decimal_val(it.get("unit_price")) or Decimal("0.00")
                it_net = _parse_decimal_val(it.get("net_amount")) or _parse_decimal_val(it.get("total_price")) or (it_qty * it_price)
                tot += it_net
        purchase_order.total_net_amount = tot.quantize(Decimal("0.01"))

    if "gst_amount" in data and data["gst_amount"] is not None:
        purchase_order.gst_amount = _parse_decimal_val(data["gst_amount"])
    elif purchase_order.gst_rate is not None and purchase_order.total_net_amount is not None and purchase_order.gst_amount is None:
        purchase_order.gst_amount = (purchase_order.total_net_amount * purchase_order.gst_rate / Decimal("100")).quantize(Decimal("0.01"))

    if "total_gross_amount" in data and data["total_gross_amount"] is not None:
        purchase_order.total_gross_amount = _parse_decimal_val(data["total_gross_amount"])
    elif purchase_order.total_net_amount is not None and purchase_order.total_gross_amount is None:
        purchase_order.total_gross_amount = (purchase_order.total_net_amount + (purchase_order.gst_amount or Decimal("0.00"))).quantize(Decimal("0.01"))
    if "remark" in data or "remarks" in data:
        purchase_order.remark = normalize_remark_for_db(
            data.get("remark") if "remark" in data else data.get("remarks")
        )

    if "items" in data and data["items"] is not None:
        _replace_items(purchase_order, data["items"])

    return purchase_order


def delete_purchase_order(purchase_order: PurchaseOrder) -> None:
    db.session.delete(purchase_order)

