import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import (
    Project,
    Supplier,
    SupplierOrderConfirmation,
    SupplierProformaInvoice,
    SupplierProformaInvoiceItem,
)


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


def get_order_confirmation(order_confirmation_id: int) -> SupplierOrderConfirmation | None:
    return db.session.get(SupplierOrderConfirmation, order_confirmation_id)


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
    invoice: SupplierProformaInvoice,
    items: list[dict],
) -> None:
    invoice.items.clear()
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

        item_obj = SupplierProformaInvoiceItem(
            material_name=mat_name,
            description=desc,
            hsn_code=hsn,
            quantity=qty,
            unit_price=unit_price,
            net_amount=net_amt,
        )
        invoice.items.append(item_obj)


def create_supplier_proforma_invoice(*, data: dict) -> SupplierProformaInvoice:
    invoice_date_val = _parse_date_val(
        data.get("proforma_invoice_date") or data.get("invoice_date")
    )
    delivery_date_val = _parse_date_val(data.get("delivery_date"))

    invoice = SupplierProformaInvoice(
        project_id=data["project_id"],
        supplier_id=data["supplier_id"],
        order_confirmation_id=data.get("order_confirmation_id"),
        proforma_invoice_no=str(
            data.get("proforma_invoice_no") or data.get("proforma_invoice_number")
        ).strip(),
        proforma_invoice_date=invoice_date_val,
        delivery_terms=_normalize_optional_string(
            data.get("delivery_terms") or data.get("delivery_term")
        ),
        delivery_period=_normalize_optional_string(
            data.get("delivery_period")
        ),
        delivery_date=delivery_date_val,
        payment_terms=_normalize_optional_string(
            data.get("payment_terms") or data.get("payment_term")
        ),
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
        total_amount=_parse_decimal_val(data.get("total_amount")),
        total_net_amount=_parse_decimal_val(data.get("total_net_amount")),
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    items_data = data.get("items") or []
    _replace_items(invoice, items_data)

    db.session.add(invoice)
    return invoice


def get_supplier_proforma_invoice(invoice_id: int) -> SupplierProformaInvoice | None:
    return (
        SupplierProformaInvoice.query.options(selectinload(SupplierProformaInvoice.items))
        .filter(SupplierProformaInvoice.id == invoice_id)
        .first()
    )


def get_supplier_proforma_invoice_by_project(project_id: int) -> SupplierProformaInvoice | None:
    return (
        SupplierProformaInvoice.query.options(selectinload(SupplierProformaInvoice.items))
        .filter(SupplierProformaInvoice.project_id == project_id)
        .order_by(SupplierProformaInvoice.id.desc())
        .first()
    )


def list_supplier_proforma_invoices(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
    proforma_invoice_no: str | None = None,
) -> list[SupplierProformaInvoice]:
    query = SupplierProformaInvoice.query.options(
        selectinload(SupplierProformaInvoice.items)
    )
    if project_id is not None:
        query = query.filter(SupplierProformaInvoice.project_id == project_id)
    if supplier_id is not None:
        query = query.filter(SupplierProformaInvoice.supplier_id == supplier_id)
    if proforma_invoice_no:
        query = query.filter(
            SupplierProformaInvoice.proforma_invoice_no.ilike(f"%{proforma_invoice_no.strip()}%")
        )

    return query.order_by(SupplierProformaInvoice.id.desc()).all()


def update_supplier_proforma_invoice(
    *,
    invoice: SupplierProformaInvoice,
    data: dict,
) -> SupplierProformaInvoice:
    if "project_id" in data:
        invoice.project_id = data["project_id"]
    if "supplier_id" in data:
        invoice.supplier_id = data["supplier_id"]
    if "order_confirmation_id" in data:
        invoice.order_confirmation_id = data["order_confirmation_id"]

    if "proforma_invoice_no" in data or "proforma_invoice_number" in data:
        invoice.proforma_invoice_no = str(
            data.get("proforma_invoice_no") or data.get("proforma_invoice_number")
        ).strip()

    if "proforma_invoice_date" in data or "invoice_date" in data:
        dt = _parse_date_val(data.get("proforma_invoice_date") or data.get("invoice_date"))
        if dt is not None:
            invoice.proforma_invoice_date = dt

    if "delivery_terms" in data or "delivery_term" in data:
        invoice.delivery_terms = _normalize_optional_string(
            data.get("delivery_terms") or data.get("delivery_term")
        )

    if "delivery_period" in data:
        invoice.delivery_period = _normalize_optional_string(data.get("delivery_period"))

    if "delivery_date" in data:
        invoice.delivery_date = _parse_date_val(data.get("delivery_date"))

    if "payment_terms" in data or "payment_term" in data:
        invoice.payment_terms = _normalize_optional_string(
            data.get("payment_terms") or data.get("payment_term")
        )

    if "warranty_period" in data:
        invoice.warranty_period = _normalize_optional_string(data.get("warranty_period"))

    if "total_amount" in data:
        invoice.total_amount = _parse_decimal_val(data.get("total_amount"))

    if "total_net_amount" in data:
        invoice.total_net_amount = _parse_decimal_val(data.get("total_net_amount"))

    if "remark" in data or "remarks" in data:
        invoice.remark = _normalize_optional_string(data.get("remark") or data.get("remarks"))

    if "items" in data and data["items"] is not None:
        _replace_items(invoice, data["items"])

    invoice.updated_at = datetime.utcnow()
    return invoice


def delete_supplier_proforma_invoice(invoice_id: int) -> list[str]:
    invoice = get_supplier_proforma_invoice(invoice_id)
    if invoice is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type="supplier_proforma_invoice",
        entity_id=invoice_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(invoice)
    return storage_keys

