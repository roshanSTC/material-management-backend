import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import Customer, CustomerTender, CustomerTenderItem, Project


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_customer(customer_id: int) -> Customer | None:
    return db.session.get(Customer, customer_id)


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _parse_datetime_val(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    s = str(val).strip()
    if not s:
        return None
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    return datetime.fromisoformat(s)


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


def _replace_items(customer_tender: CustomerTender, items: list[dict]) -> None:
    customer_tender.items.clear()
    for item in items:
        desc = (
            item.get("description")
            or item.get("material_name")
            or ""
        )
        quantity_val = _parse_decimal_val(item.get("quantity")) or Decimal("1")
        item_code_val = _normalize_optional_string(item.get("item_code"))

        tender_item = CustomerTenderItem(
            item_code=item_code_val,
            description=desc,
            quantity=quantity_val,
        )
        customer_tender.items.append(tender_item)


def create_customer_tender(*, data: dict) -> CustomerTender:
    tender = CustomerTender(
        project_id=data["project_id"],
        customer_id=data.get("customer_id"),
        officer_name=_normalize_optional_string(
            data.get("officer_name") or data.get("company_business_name")
        ),
        email=_normalize_optional_string(data.get("email")),
        address=_normalize_optional_string(data.get("address")),
        website=_normalize_optional_string(data.get("website")),
        contact_number=_normalize_optional_string(data.get("contact_number")),
        tender_title=_normalize_optional_string(data.get("tender_title")),
        tender_number=str(data["tender_number"]).strip(),
        tender_date=_parse_datetime_val(data.get("tender_date")),
        opening_date_time=_parse_datetime_val(data.get("opening_date_time")),
        closing_date_time=_parse_datetime_val(data.get("closing_date_time")),
        tender_fee=_parse_decimal_val(data.get("tender_fee")),
        validity=_normalize_optional_string(data.get("validity")),
        delivery_terms=_normalize_optional_string(
            data.get("delivery_terms") or data.get("incoterms")
        ),
        delivery_period=_normalize_optional_string(data.get("delivery_period")),
        payment_terms=_normalize_optional_string(data.get("payment_terms")),
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
        remark=_normalize_optional_string(
            data.get("remark") or data.get("remarks")
        ),
    )

    if "items" in data and data["items"]:
        _replace_items(tender, data["items"])

    db.session.add(tender)
    db.session.flush()
    return tender


def get_customer_tender(customer_tender_id: int) -> CustomerTender | None:
    return db.session.execute(
        db.select(CustomerTender)
        .options(selectinload(CustomerTender.items))
        .where(CustomerTender.id == customer_tender_id)
    ).scalar_one_or_none()


def list_customer_tenders(
    *,
    project_id: int | None = None,
) -> list[CustomerTender]:
    statement = db.select(CustomerTender).options(
        selectinload(CustomerTender.items)
    )
    if project_id is not None:
        statement = statement.where(CustomerTender.project_id == project_id)

    return db.session.execute(
        statement.order_by(CustomerTender.id.desc())
    ).scalars().all()


def get_latest_customer_tender_for_project(project_id: int) -> CustomerTender | None:
    return db.session.execute(
        db.select(CustomerTender)
        .options(selectinload(CustomerTender.items))
        .where(CustomerTender.project_id == project_id)
        .order_by(CustomerTender.id.desc())
    ).scalars().first()


def update_customer_tender(
    customer_tender: CustomerTender,
    *,
    data: dict,
) -> CustomerTender:
    if "project_id" in data:
        customer_tender.project_id = data["project_id"]
    if "customer_id" in data:
        customer_tender.customer_id = data["customer_id"]
    if "officer_name" in data or "company_business_name" in data:
        customer_tender.officer_name = _normalize_optional_string(
            data.get("officer_name") or data.get("company_business_name")
        )
    if "email" in data:
        customer_tender.email = _normalize_optional_string(data["email"])
    if "address" in data:
        customer_tender.address = _normalize_optional_string(data["address"])
    if "website" in data:
        customer_tender.website = _normalize_optional_string(data["website"])
    if "contact_number" in data:
        customer_tender.contact_number = _normalize_optional_string(data["contact_number"])
    if "tender_title" in data:
        customer_tender.tender_title = _normalize_optional_string(data["tender_title"])
    if "tender_number" in data and data["tender_number"] is not None:
        customer_tender.tender_number = str(data["tender_number"]).strip()
    if "tender_date" in data:
        customer_tender.tender_date = _parse_datetime_val(data["tender_date"])
    if "opening_date_time" in data:
        customer_tender.opening_date_time = _parse_datetime_val(data["opening_date_time"])
    if "closing_date_time" in data:
        customer_tender.closing_date_time = _parse_datetime_val(data["closing_date_time"])
    if "tender_fee" in data:
        customer_tender.tender_fee = _parse_decimal_val(data["tender_fee"])
    if "validity" in data:
        customer_tender.validity = _normalize_optional_string(data["validity"])
    if "delivery_terms" in data or "incoterms" in data:
        customer_tender.delivery_terms = _normalize_optional_string(
            data.get("delivery_terms") or data.get("incoterms")
        )
    if "delivery_period" in data:
        customer_tender.delivery_period = _normalize_optional_string(data["delivery_period"])
    if "payment_terms" in data:
        customer_tender.payment_terms = _normalize_optional_string(data["payment_terms"])
    if "warranty_period" in data:
        customer_tender.warranty_period = _normalize_optional_string(data["warranty_period"])
    if "remark" in data or "remarks" in data:
        customer_tender.remark = _normalize_optional_string(
            data.get("remark") or data.get("remarks")
        )

    if "items" in data and data["items"] is not None:
        _replace_items(customer_tender, data["items"])

    return customer_tender


def delete_customer_tender(customer_tender: CustomerTender) -> None:
    db.session.delete(customer_tender)

