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
    for idx, item in enumerate(items, start=1):
        desc = _normalize_optional_string(item.get("description")) or ""
        hsn = _normalize_optional_string(item.get("hsn_sac"))
        qty = _parse_decimal_val(item.get("quantity")) or Decimal("1")
        unit_price = _parse_decimal_val(item.get("unit_price"))
        if unit_price is None:
            unit_price = Decimal("0.00")

        total_price = _parse_decimal_val(item.get("total_price"))
        if total_price is None and unit_price is not None and qty is not None:
            total_price = (qty * unit_price).quantize(Decimal("0.01"))

        unit_str = _normalize_optional_string(item.get("unit")) or "NOS"
        item_delivery_date = _parse_date_val(item.get("delivery_date")) or purchase_order.delivery_date

        po_item = PurchaseOrderItem(
            sr_no=item.get("sr_no") if item.get("sr_no") is not None else idx,
            description=desc,
            hsn_sac=hsn,
            quantity=qty,
            unit_price=unit_price,
            total_price=total_price,
            currency=_normalize_optional_string(item.get("currency")),
            unit=unit_str,
            delivery_date=item_delivery_date,
        )
        purchase_order.items.append(po_item)


def create_purchase_order(*, data: dict) -> PurchaseOrder:
    po_num = str(data.get("po_no") or "").strip()
    gst_rate_val = _parse_decimal_val(data.get("gst_rate_pct"))

    del_date_val = _parse_date_val(data.get("delivery_date"))
    if del_date_val is None and data.get("items"):
        for it in data["items"]:
            if isinstance(it, dict):
                parsed = _parse_date_val(it.get("delivery_date"))
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
                it_net = _parse_decimal_val(it.get("total_price")) or (it_qty * it_price)
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
        customer_name=_normalize_optional_string(data.get("customer_name")),
        tender_id=data.get("tender_id"),
        po_title=_normalize_optional_string(data.get("po_title")) or "",
        po_no=po_num,
        poc_name=_normalize_optional_string(data.get("poc_name")),
        email=_normalize_optional_string(data.get("email")),
        contact=_normalize_optional_string(data.get("contact")),
        po_date=_parse_date_val(data.get("po_date")),
        delivery_date=del_date_val,
        delivery_terms=_normalize_optional_string(data.get("delivery_terms")),
        payment_terms=_normalize_optional_string(data.get("payment_terms")),
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
        gst_rate_pct=gst_rate_val,
        gst_amount=gst_amt_val,
        total_net_amount=net_amt_val,
        total_gross_amount=gross_amt_val,
        currency_unit=_normalize_optional_string(data.get("currency_unit")),
        currency_symbol=_normalize_optional_string(data.get("currency_symbol")),
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
    po_no: str | None = None,
) -> list[PurchaseOrder]:
    statement = db.select(PurchaseOrder).options(
        selectinload(PurchaseOrder.items)
    )
    if project_id is not None:
        statement = statement.where(PurchaseOrder.project_id == project_id)
    if customer_id is not None:
        statement = statement.where(PurchaseOrder.customer_id == customer_id)
    if po_no is not None:
        statement = statement.where(PurchaseOrder.po_no.ilike(f"%{po_no}%"))

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
    if "customer_name" in data:
        purchase_order.customer_name = _normalize_optional_string(data["customer_name"])
    if "tender_id" in data:
        purchase_order.tender_id = data["tender_id"]
    if "po_title" in data and data["po_title"] is not None:
        purchase_order.po_title = _normalize_optional_string(data["po_title"]) or ""
    if "po_no" in data and data["po_no"] is not None:
        purchase_order.po_no = str(data["po_no"]).strip()
    if "poc_name" in data:
        purchase_order.poc_name = _normalize_optional_string(data["poc_name"])
    if "email" in data:
        purchase_order.email = _normalize_optional_string(data["email"])
    if "contact" in data:
        purchase_order.contact = _normalize_optional_string(data["contact"])
    if "po_date" in data:
        purchase_order.po_date = _parse_date_val(data["po_date"])
    if "delivery_date" in data:
        del_date_val = _parse_date_val(data["delivery_date"])
        if del_date_val is not None:
            purchase_order.delivery_date = del_date_val
    elif purchase_order.delivery_date is None and data.get("items"):
        for it in data["items"]:
            if isinstance(it, dict):
                parsed = _parse_date_val(it.get("delivery_date"))
                if parsed:
                    purchase_order.delivery_date = parsed
                    break

    if "delivery_terms" in data:
        purchase_order.delivery_terms = _normalize_optional_string(data["delivery_terms"])
    if "payment_terms" in data:
        purchase_order.payment_terms = _normalize_optional_string(data["payment_terms"])
    if "warranty_period" in data:
        purchase_order.warranty_period = _normalize_optional_string(data["warranty_period"])

    if "gst_rate_pct" in data:
        purchase_order.gst_rate_pct = _parse_decimal_val(data["gst_rate_pct"])
    if "currency_unit" in data:
        purchase_order.currency_unit = _normalize_optional_string(data["currency_unit"])
    if "currency_symbol" in data:
        purchase_order.currency_symbol = _normalize_optional_string(data["currency_symbol"])

    if "items" in data and data["items"] is not None:
        _replace_items(purchase_order, data["items"])

    # If items were provided and caller did not pass an explicit total_net_amount, recalculate from items
    if ("items" in data and data["items"] is not None and ("total_net_amount" not in data or data.get("total_net_amount") is None)) or (
        purchase_order.total_net_amount is None and purchase_order.items
    ):
        items_net = Decimal("0.00")
        for it in purchase_order.items:
            items_net += (it.total_price or Decimal("0.00"))
        purchase_order.total_net_amount = items_net.quantize(Decimal("0.01"))
    elif "total_net_amount" in data and data["total_net_amount"] is not None:
        purchase_order.total_net_amount = _parse_decimal_val(data["total_net_amount"])

    # If items or gst were updated and caller did not pass an explicit gst_amount, recalculate
    if ("items" in data and data["items"] is not None and ("gst_amount" not in data or data.get("gst_amount") is None)) or (
        purchase_order.gst_amount is None and purchase_order.gst_rate_pct is not None and purchase_order.total_net_amount is not None
    ):
        if purchase_order.gst_rate_pct is not None and purchase_order.total_net_amount is not None:
            purchase_order.gst_amount = (
                purchase_order.total_net_amount * purchase_order.gst_rate_pct / Decimal("100")
            ).quantize(Decimal("0.01"))
    elif "gst_amount" in data and data["gst_amount"] is not None:
        purchase_order.gst_amount = _parse_decimal_val(data["gst_amount"])

    # If items were updated and caller did not pass an explicit total_gross_amount, recalculate
    if ("items" in data and data["items"] is not None and ("total_gross_amount" not in data or data.get("total_gross_amount") is None)) or (
        purchase_order.total_gross_amount is None and purchase_order.total_net_amount is not None
    ):
        if purchase_order.total_net_amount is not None:
            purchase_order.total_gross_amount = (
                purchase_order.total_net_amount + (purchase_order.gst_amount or Decimal("0.00"))
            ).quantize(Decimal("0.01"))
    elif "total_gross_amount" in data and data["total_gross_amount"] is not None:
        purchase_order.total_gross_amount = _parse_decimal_val(data["total_gross_amount"])

    if "remark" in data or "remarks" in data:
        purchase_order.remark = normalize_remark_for_db(
            data.get("remark") if "remark" in data else data.get("remarks")
        )

    return purchase_order


def delete_purchase_order(purchase_order: PurchaseOrder) -> None:
    db.session.delete(purchase_order)

