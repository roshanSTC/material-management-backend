import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import (
    CustomerDeliveryInvoice,
    CustomerDeliveryInvoiceItem,
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
    invoice: CustomerDeliveryInvoice,
    items: list[dict],
) -> None:
    invoice.items.clear()
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

        item_obj = CustomerDeliveryInvoiceItem(
            material_name=mat_name,
            hsn_code=hsn,
            quantity=qty,
            unit_price=unit_price,
            net_amount=net_amt,
        )
        invoice.items.append(item_obj)


def create_customer_delivery_invoice(*, data: dict) -> CustomerDeliveryInvoice:
    invoice_date_val = _parse_date_val(data.get("invoice_date"))

    invoice = CustomerDeliveryInvoice(
        project_id=data["project_id"],
        invoice_no=str(
            data.get("invoice_no") or data.get("invoice_number")
        ).strip(),
        invoice_date=invoice_date_val,
        gst_rate=_parse_decimal_val(data.get("gst_rate")),
        gst_amount=_parse_decimal_val(data.get("gst_amount")),
        round_off=_parse_decimal_val(data.get("round_off")),
        net_total=_parse_decimal_val(data.get("net_total")),
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    items_data = data.get("items") or []
    _replace_items(invoice, items_data)

    db.session.add(invoice)
    return invoice


def get_customer_delivery_invoice(invoice_id: int) -> CustomerDeliveryInvoice | None:
    return (
        CustomerDeliveryInvoice.query.options(
            selectinload(CustomerDeliveryInvoice.items)
        )
        .filter(CustomerDeliveryInvoice.id == invoice_id)
        .first()
    )


def list_customer_delivery_invoices(
    *,
    project_id: int | None = None,
    invoice_no: str | None = None,
) -> list[CustomerDeliveryInvoice]:
    query = CustomerDeliveryInvoice.query.options(
        selectinload(CustomerDeliveryInvoice.items)
    )
    if project_id is not None:
        query = query.filter(CustomerDeliveryInvoice.project_id == project_id)
    if invoice_no:
        query = query.filter(
            CustomerDeliveryInvoice.invoice_no.ilike(f"%{invoice_no.strip()}%")
        )

    return query.order_by(CustomerDeliveryInvoice.id.desc()).all()


def update_customer_delivery_invoice(
    *,
    invoice: CustomerDeliveryInvoice,
    data: dict,
) -> CustomerDeliveryInvoice:
    if "project_id" in data:
        invoice.project_id = data["project_id"]

    if "invoice_no" in data or "invoice_number" in data:
        invoice.invoice_no = str(
            data.get("invoice_no") or data.get("invoice_number")
        ).strip()

    if "invoice_date" in data:
        dt = _parse_date_val(data.get("invoice_date"))
        if dt is not None:
            invoice.invoice_date = dt

    if "gst_rate" in data:
        invoice.gst_rate = _parse_decimal_val(data.get("gst_rate"))

    if "gst_amount" in data:
        invoice.gst_amount = _parse_decimal_val(data.get("gst_amount"))

    if "round_off" in data:
        invoice.round_off = _parse_decimal_val(data.get("round_off"))

    if "net_total" in data:
        invoice.net_total = _parse_decimal_val(data.get("net_total"))

    if "remark" in data or "remarks" in data:
        invoice.remark = _normalize_optional_string(
            data.get("remark") or data.get("remarks")
        )

    if "items" in data and data["items"] is not None:
        _replace_items(invoice, data["items"])

    invoice.updated_at = datetime.utcnow()
    return invoice


def delete_customer_delivery_invoice(invoice_id: int) -> list[str]:
    invoice = get_customer_delivery_invoice(invoice_id)
    if invoice is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type="customer_delivery_invoice",
        entity_id=invoice_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(invoice)
    return storage_keys

