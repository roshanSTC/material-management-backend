import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import Customer, CustomerQuotation, CustomerQuotationItem, Project


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_customer(customer_id: int) -> Customer | None:
    return db.session.get(Customer, customer_id)


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def _parse_date_val(val):
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    return date.fromisoformat(s)


def _parse_decimal_val(val):
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


def _replace_items(customer_quotation: CustomerQuotation, items: list[dict]) -> None:
    customer_quotation.items.clear()
    for item in items:
        unit_price = _parse_decimal_val(item.get("unit_price"))
        net_amount = _parse_decimal_val(item.get("net_amount"))
        customs_duty_rate = item.get("customs_duty_rate")
        if customs_duty_rate is not None:
            customs_duty_rate = Decimal(str(customs_duty_rate))

        customer_quotation.items.append(
            CustomerQuotationItem(
                cost_sheet_item_id=item.get("cost_sheet_item_id"),
                quotation_number=_normalize_optional_string(item.get("quotation_number")),
                item_code=_normalize_optional_string(item.get("item_code")),
                material_name=str(item["material_name"]).strip(),
                quantity=Decimal(str(item["quantity"])),
                unit_price=unit_price,
                net_amount=net_amount,
                customs_duty_rate=customs_duty_rate,
            )
        )


def create_customer_quotation(*, data: dict) -> CustomerQuotation:
    q_num = data.get("quotation_number") or data.get("qo_number")
    q_date = _parse_date_val(data.get("quotation_date"))
    q_val = _parse_decimal_val(data.get("quotation_value"))
    total_net = _parse_decimal_val(data.get("total_net_amount"))

    customer_quotation = CustomerQuotation(
        project_id=data["project_id"],
        customer_id=data["customer_id"],
        qo_number=_normalize_optional_string(q_num),
        quotation_number=_normalize_optional_string(q_num),
        quotation_date=q_date,
        quotation_value=q_val,
        currency_unit=_normalize_optional_string(data.get("currency_unit")),
        currency_symbol=_normalize_optional_string(data.get("currency_symbol")),
        total_net_amount=total_net,
        validity=_normalize_optional_string(data.get("validity")),
        remark=_normalize_optional_string(data.get("remark") or data.get("remarks")),
    )
    if "items" in data and data["items"]:
        _replace_items(customer_quotation, data["items"])

    db.session.add(customer_quotation)
    return customer_quotation


def get_customer_quotation(customer_quotation_id: int) -> CustomerQuotation | None:
    return db.session.execute(
        db.select(CustomerQuotation)
        .options(selectinload(CustomerQuotation.items))
        .where(CustomerQuotation.id == customer_quotation_id)
    ).scalar_one_or_none()


def list_customer_quotations(
    *,
    project_id: int | None = None,
    customer_id: int | None = None,
    quotation_number: str | None = None,
) -> list[CustomerQuotation]:
    statement = db.select(CustomerQuotation).options(
        selectinload(CustomerQuotation.items)
    )
    if project_id is not None:
        statement = statement.where(CustomerQuotation.project_id == project_id)
    if customer_id is not None:
        statement = statement.where(CustomerQuotation.customer_id == customer_id)
    if quotation_number:
        clean_q = f"%{quotation_number.strip()}%"
        statement = statement.where(
            db.or_(
                CustomerQuotation.quotation_number.ilike(clean_q),
                CustomerQuotation.qo_number.ilike(clean_q),
            )
        )

    return db.session.execute(
        statement.order_by(CustomerQuotation.id.desc())
    ).scalars().all()


def update_customer_quotation(
    customer_quotation: CustomerQuotation,
    *,
    data: dict,
) -> CustomerQuotation:
    if "project_id" in data:
        customer_quotation.project_id = data["project_id"]
    if "customer_id" in data:
        customer_quotation.customer_id = data["customer_id"]
    if "quotation_number" in data or "qo_number" in data:
        q_num = _normalize_optional_string(data.get("quotation_number") or data.get("qo_number"))
        customer_quotation.quotation_number = q_num
        customer_quotation.qo_number = q_num
    if "quotation_date" in data:
        customer_quotation.quotation_date = _parse_date_val(data["quotation_date"])
    if "quotation_value" in data:
        customer_quotation.quotation_value = _parse_decimal_val(data["quotation_value"])
    if "currency_unit" in data:
        customer_quotation.currency_unit = _normalize_optional_string(data["currency_unit"])
    if "currency_symbol" in data:
        customer_quotation.currency_symbol = _normalize_optional_string(data["currency_symbol"])
    if "total_net_amount" in data:
        customer_quotation.total_net_amount = _parse_decimal_val(data["total_net_amount"])
    if "validity" in data:
        customer_quotation.validity = _normalize_optional_string(data["validity"])
    if "remark" in data or "remarks" in data:
        customer_quotation.remark = _normalize_optional_string(data.get("remark") or data.get("remarks"))

    if "items" in data and data["items"] is not None:
        _replace_items(customer_quotation, data["items"])

    return customer_quotation


def delete_customer_quotation(customer_quotation: CustomerQuotation) -> None:
    db.session.delete(customer_quotation)

