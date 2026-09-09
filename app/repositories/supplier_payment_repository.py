from datetime import date, datetime
from decimal import Decimal
import re

from app.extensions.database import db
from app.models import Project, Supplier, SupplierPayment


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


def create_supplier_payment(*, data: dict) -> SupplierPayment:
    pay_date = _parse_date_val(data.get("payment_date"))

    payment = SupplierPayment(
        project_id=data["project_id"],
        supplier_id=data.get("supplier_id"),
        currency=str(data.get("currency") or "INR").strip().upper(),
        payment_percentage=_parse_decimal_val(data.get("payment_percentage")),
        total_supplier_value=_parse_decimal_val(data.get("total_supplier_value")),
        amount_paid=_parse_decimal_val(data.get("amount_paid")),
        payment_date=pay_date,
        transaction_details=_normalize_optional_string(data.get("transaction_details")),
        pending_amount=_parse_decimal_val(data.get("pending_amount")),
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(payment)
    return payment


def get_supplier_payment(payment_id: int) -> SupplierPayment | None:
    return db.session.get(SupplierPayment, payment_id)


def list_supplier_payments(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
    currency: str | None = None,
) -> list[SupplierPayment]:
    query = SupplierPayment.query
    if project_id is not None:
        query = query.filter(SupplierPayment.project_id == project_id)
    if supplier_id is not None:
        query = query.filter(SupplierPayment.supplier_id == supplier_id)
    if currency:
        query = query.filter(SupplierPayment.currency == currency.strip().upper())
    return query.order_by(SupplierPayment.id.desc()).all()


def update_supplier_payment(
    *,
    payment: SupplierPayment,
    data: dict,
) -> SupplierPayment:
    if "project_id" in data and data["project_id"] is not None:
        payment.project_id = data["project_id"]

    if "supplier_id" in data:
        payment.supplier_id = data["supplier_id"]

    if "currency" in data and data["currency"] is not None:
        payment.currency = str(data["currency"]).strip().upper()

    if "payment_percentage" in data:
        payment.payment_percentage = _parse_decimal_val(data.get("payment_percentage"))

    if "total_supplier_value" in data:
        payment.total_supplier_value = _parse_decimal_val(data.get("total_supplier_value"))

    if "amount_paid" in data:
        payment.amount_paid = _parse_decimal_val(data.get("amount_paid"))

    if "payment_date" in data:
        dt = _parse_date_val(data.get("payment_date"))
        if dt is not None:
            payment.payment_date = dt

    if "transaction_details" in data:
        payment.transaction_details = _normalize_optional_string(data.get("transaction_details"))

    if "pending_amount" in data:
        payment.pending_amount = _parse_decimal_val(data.get("pending_amount"))

    if "remark" in data or "remarks" in data:
        payment.remark = _normalize_optional_string(data.get("remark") or data.get("remarks"))

    payment.updated_at = datetime.utcnow()
    return payment


def delete_supplier_payment(payment_id: int) -> list[str]:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type="supplier_payment",
        entity_id=payment_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(payment)
    return storage_keys
