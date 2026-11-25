from datetime import date, datetime
from decimal import Decimal
import re

from app.extensions.database import db
from app.models import CustomerPayment, Project


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


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
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
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
    pay_date = _parse_date_val(data.get("payment_received_date"))

    payment = CustomerPayment(
        project_id=data["project_id"],
        payment_against_invoice_no=str(data["payment_against_invoice_no"]).strip(),
        invoice_date=inv_date,
        invoice_value=_parse_decimal_val(data.get("invoice_value")),
        payment_received=_parse_decimal_val(data.get("payment_received")),
        payment_received_date=pay_date,
        tds_deducted=_parse_decimal_val(data.get("tds_deducted")),
        ld_deducted=_parse_decimal_val(data.get("ld_deducted")),
        balance_amount=_parse_decimal_val(data.get("balance_amount")),
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(payment)
    return payment


def get_customer_payment(payment_id: int) -> CustomerPayment | None:
    return db.session.get(CustomerPayment, payment_id)


def get_total_previously_paid(project_id: int, exclude_id: int | None = None) -> Decimal:
    query = db.session.query(
        db.func.coalesce(
            db.func.sum(
                db.func.coalesce(CustomerPayment.payment_received, 0)
                + db.func.coalesce(CustomerPayment.tds_deducted, 0)
                + db.func.coalesce(CustomerPayment.ld_deducted, 0)
            ),
            0,
        )
    ).filter(CustomerPayment.project_id == project_id)
    if exclude_id is not None:
        query = query.filter(CustomerPayment.id != exclude_id)
    val = query.scalar()
    return Decimal(str(val or 0))


def get_latest_customer_payment_for_project(project_id: int) -> CustomerPayment | None:
    return (
        CustomerPayment.query.filter_by(project_id=project_id)
        .order_by(CustomerPayment.created_at.desc(), CustomerPayment.id.desc())
        .first()
    )


def list_customer_payments(
    *,
    project_id: int | None = None,
    payment_against_invoice_no: str | None = None,
    latest_first: bool = False,
) -> list[CustomerPayment]:
    query = CustomerPayment.query
    if project_id is not None:
        query = query.filter(CustomerPayment.project_id == project_id)
    if payment_against_invoice_no:
        query = query.filter(
            CustomerPayment.payment_against_invoice_no.ilike(f"%{payment_against_invoice_no.strip()}%")
        )
    if latest_first:
        return query.order_by(
            CustomerPayment.created_at.desc(),
            CustomerPayment.id.desc(),
        ).all()
    return query.order_by(
        CustomerPayment.created_at.asc(),
        CustomerPayment.id.asc(),
    ).all()


def update_customer_payment(
    *,
    payment: CustomerPayment,
    data: dict,
) -> CustomerPayment:
    if "project_id" in data and data["project_id"] is not None:
        payment.project_id = data["project_id"]

    if "payment_against_invoice_no" in data and data["payment_against_invoice_no"] is not None:
        payment.payment_against_invoice_no = str(data["payment_against_invoice_no"]).strip()

    if "invoice_date" in data:
        dt = _parse_date_val(data.get("invoice_date"))
        if dt is not None:
            payment.invoice_date = dt

    if "invoice_value" in data:
        payment.invoice_value = _parse_decimal_val(data.get("invoice_value"))

    if "payment_received" in data:
        payment.payment_received = _parse_decimal_val(data.get("payment_received"))

    if "payment_received_date" in data:
        dt = _parse_date_val(data.get("payment_received_date"))
        if dt is not None:
            payment.payment_received_date = dt

    if "tds_deducted" in data:
        payment.tds_deducted = _parse_decimal_val(data.get("tds_deducted"))

    if "ld_deducted" in data:
        payment.ld_deducted = _parse_decimal_val(data.get("ld_deducted"))

    if "balance_amount" in data:
        payment.balance_amount = _parse_decimal_val(data.get("balance_amount"))

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
