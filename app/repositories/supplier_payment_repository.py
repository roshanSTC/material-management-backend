from datetime import date, datetime
from decimal import Decimal
import re

from app.extensions.database import db
from app.models import Project, Supplier, SupplierPayment


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


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
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
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


def create_supplier_payment(*, data: dict) -> SupplierPayment:
    pay_date = _parse_date_val(data.get("payment_date"))
    bcc = _normalize_optional_string(data.get("bank_charges_currency"))

    payment = SupplierPayment(
        project_id=data["project_id"],
        supplier_id=data.get("supplier_id"),
        currency=str(data.get("currency") or "INR").strip().upper(),
        payment_pct=_parse_decimal_val(data.get("payment_pct")),
        total_contract_value=_parse_decimal_val(data.get("total_contract_value")),
        payment_amount=_parse_decimal_val(data.get("payment_amount")),
        payment_date=pay_date,
        reference_no=_normalize_optional_string(data.get("reference_no")),
        pending_amount=_parse_decimal_val(data.get("pending_amount")),
        eur_to_inr_rate=_parse_decimal_val(data.get("eur_to_inr_rate")),
        payment_amount_inr=_parse_decimal_val(data.get("payment_amount_inr")),
        bank_charges_currency=bcc.upper() if bcc else None,
        bank_charges=_parse_decimal_val(data.get("bank_charges")),
        swift_charges=_parse_decimal_val(data.get("swift_charges")),
        total_outflow=_parse_decimal_val(data.get("total_outflow")),
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(payment)
    return payment


def get_supplier_payment(payment_id: int) -> SupplierPayment | None:
    return db.session.get(SupplierPayment, payment_id)


def get_total_previously_paid(project_id: int, exclude_id: int | None = None) -> Decimal:
    query = db.session.query(
        db.func.coalesce(db.func.sum(SupplierPayment.payment_amount), 0)
    ).filter(SupplierPayment.project_id == project_id)
    if exclude_id is not None:
        query = query.filter(SupplierPayment.id != exclude_id)
    val = query.scalar()
    return Decimal(str(val or 0))


def get_latest_supplier_payment_for_project(project_id: int) -> SupplierPayment | None:
    return (
        SupplierPayment.query.filter_by(project_id=project_id)
        .order_by(SupplierPayment.created_at.desc(), SupplierPayment.id.desc())
        .first()
    )


def list_supplier_payments(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
    currency: str | None = None,
    latest_first: bool = False,
) -> list[SupplierPayment]:
    query = SupplierPayment.query
    if project_id is not None:
        query = query.filter(SupplierPayment.project_id == project_id)
    if supplier_id is not None:
        query = query.filter(SupplierPayment.supplier_id == supplier_id)
    if currency:
        query = query.filter(SupplierPayment.currency == currency.strip().upper())
    if latest_first:
        return query.order_by(
            SupplierPayment.created_at.desc(),
            SupplierPayment.id.desc(),
        ).all()
    return query.order_by(
        SupplierPayment.created_at.asc(),
        SupplierPayment.id.asc(),
    ).all()


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

    if "payment_pct" in data:
        payment.payment_pct = _parse_decimal_val(data.get("payment_pct"))

    if "total_contract_value" in data:
        payment.total_contract_value = _parse_decimal_val(data.get("total_contract_value"))

    if "payment_amount" in data:
        payment.payment_amount = _parse_decimal_val(data.get("payment_amount"))

    if "payment_date" in data:
        dt = _parse_date_val(data.get("payment_date"))
        if dt is not None:
            payment.payment_date = dt

    if "reference_no" in data:
        payment.reference_no = _normalize_optional_string(data.get("reference_no"))

    if "pending_amount" in data:
        payment.pending_amount = _parse_decimal_val(data.get("pending_amount"))

    if "eur_to_inr_rate" in data:
        payment.eur_to_inr_rate = _parse_decimal_val(data.get("eur_to_inr_rate"))

    if "payment_amount_inr" in data:
        payment.payment_amount_inr = _parse_decimal_val(data.get("payment_amount_inr"))

    if "bank_charges_currency" in data:
        bcc = _normalize_optional_string(data.get("bank_charges_currency"))
        payment.bank_charges_currency = bcc.upper() if bcc else None

    if "bank_charges" in data:
        payment.bank_charges = _parse_decimal_val(data.get("bank_charges"))

    if "swift_charges" in data:
        payment.swift_charges = _parse_decimal_val(data.get("swift_charges"))

    if "total_outflow" in data:
        payment.total_outflow = _parse_decimal_val(data.get("total_outflow"))

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
