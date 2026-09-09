from datetime import date, datetime
from decimal import Decimal
import re

from app.extensions.database import db
from app.models import CustomerPayment, Project


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


def create_customer_payment(*, data: dict) -> CustomerPayment:
    inv_date = _parse_date_val(data.get("invoice_date"))
    pay_date = _parse_date_val(data.get("payment_date"))

    payment = CustomerPayment(
        project_id=data["project_id"],
        invoice_no=str(data.get("invoice_no") or data.get("invoice_number")).strip(),
        invoice_date=inv_date,
        invoice_value=_parse_decimal_val(data.get("invoice_value")),
        payment_amount=_parse_decimal_val(data.get("payment_amount")),
        payment_date=pay_date,
        tds=_parse_decimal_val(data.get("tds")),
        ld=_parse_decimal_val(data.get("ld") if data.get("ld") is not None else data.get("liquidated_damages")),
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(payment)
    return payment


def get_customer_payment(payment_id: int) -> CustomerPayment | None:
    return db.session.get(CustomerPayment, payment_id)


def list_customer_payments(
    *,
    project_id: int | None = None,
    invoice_no: str | None = None,
) -> list[CustomerPayment]:
    query = CustomerPayment.query
    if project_id is not None:
        query = query.filter(CustomerPayment.project_id == project_id)
    if invoice_no:
        query = query.filter(
            CustomerPayment.invoice_no.ilike(f"%{invoice_no.strip()}%")
        )
    return query.order_by(CustomerPayment.id.desc()).all()


def update_customer_payment(
    *,
    payment: CustomerPayment,
    data: dict,
) -> CustomerPayment:
    if "project_id" in data and data["project_id"] is not None:
        payment.project_id = data["project_id"]

    if "invoice_no" in data or "invoice_number" in data:
        val = data.get("invoice_no") or data.get("invoice_number")
        if val is not None:
            payment.invoice_no = str(val).strip()

    if "invoice_date" in data:
        dt = _parse_date_val(data.get("invoice_date"))
        if dt is not None:
            payment.invoice_date = dt

    if "invoice_value" in data:
        payment.invoice_value = _parse_decimal_val(data.get("invoice_value"))

    if "payment_amount" in data:
        payment.payment_amount = _parse_decimal_val(data.get("payment_amount"))

    if "payment_date" in data:
        dt = _parse_date_val(data.get("payment_date"))
        if dt is not None:
            payment.payment_date = dt

    if "tds" in data:
        payment.tds = _parse_decimal_val(data.get("tds"))

    if "ld" in data or "liquidated_damages" in data:
        ld_val = data.get("ld") if "ld" in data else data.get("liquidated_damages")
        payment.ld = _parse_decimal_val(ld_val)

    if "remark" in data or "remarks" in data:
        payment.remark = _normalize_optional_string(data.get("remark") or data.get("remarks"))

    payment.updated_at = datetime.utcnow()
    return payment


def delete_customer_payment(payment_id: int) -> list[str]:
    payment = get_customer_payment(payment_id)
    if payment is None:
        return []

    from app.models import Attachment

    attachments = Attachment.query.filter_by(
        entity_type="customer_payment",
        entity_id=payment_id,
    ).all()

    storage_keys = []
    for att in attachments:
        if att.storage_key:
            storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(payment)
    return storage_keys
