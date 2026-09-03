from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import Project, Supplier, SupplierQuotation, SupplierQuotationItem


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


def create_supplier_quotation(*, data: dict) -> SupplierQuotation:
    currency_unit = data.get("currency_unit") or data.get("value_symbol")
    supplier_quotation = SupplierQuotation(
        project_id=data["project_id"],
        supplier_id=data["supplier_id"],
        quotation_number=data["quotation_number"].strip(),
        quotation_date=data["quotation_date"],
        quotation_value=data["quotation_value"],
        currency_unit=_normalize_optional_string(currency_unit),
        validity=_normalize_optional_string(data.get("validity")),
        incoterms=_normalize_optional_string(data.get("incoterms")),
        payment_terms=_normalize_optional_string(data.get("payment_terms")),
        delivery_period=_normalize_optional_string(data.get("delivery_period")),
        remark=_normalize_optional_string(data.get("remark")),
    )
    _replace_items(supplier_quotation, data["items"])
    db.session.add(supplier_quotation)
    return supplier_quotation


def get_supplier_quotation(
    supplier_quotation_id: int,
) -> SupplierQuotation | None:
    return db.session.execute(
        db.select(SupplierQuotation)
        .options(selectinload(SupplierQuotation.items))
        .where(SupplierQuotation.id == supplier_quotation_id)
    ).scalar_one_or_none()


def list_supplier_quotations(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
) -> list[SupplierQuotation]:
    statement = db.select(SupplierQuotation).options(
        selectinload(SupplierQuotation.items)
    )
    if project_id is not None:
        statement = statement.where(SupplierQuotation.project_id == project_id)
    if supplier_id is not None:
        statement = statement.where(SupplierQuotation.supplier_id == supplier_id)

    return db.session.execute(
        statement.order_by(SupplierQuotation.id.desc())
    ).scalars().all()


def update_supplier_quotation(
    supplier_quotation: SupplierQuotation,
    *,
    data: dict,
) -> SupplierQuotation:
    string_fields = {
        "quotation_number",
        "currency_unit",
        "validity",
        "incoterms",
        "payment_terms",
        "delivery_period",
        "remark",
    }
    scalar_fields = {
        "project_id",
        "supplier_id",
        "quotation_date",
        "quotation_value",
    }

    for field in scalar_fields:
        if field in data:
            setattr(supplier_quotation, field, data[field])

    for field in string_fields:
        if field in data:
            setattr(
                supplier_quotation,
                field,
                _normalize_optional_string(data[field]),
            )

    if "items" in data:
        _replace_items(supplier_quotation, data["items"])

    return supplier_quotation


def _replace_items(
    supplier_quotation: SupplierQuotation,
    items: list[dict],
) -> None:
    supplier_quotation.items.clear()
    for item_data in items:
        quantity = item_data["quantity"]
        unit_price = item_data.get("unit_price")
        net_amount = item_data.get("net_amount")
        if net_amount is None and unit_price is not None and quantity is not None:
            try:
                net_amount = quantity * unit_price
            except Exception:
                pass

        supplier_quotation.items.append(
            SupplierQuotationItem(
                material_name=item_data["material_name"].strip(),
                quantity=quantity,
                unit_price=unit_price,
                net_amount=net_amount,
            )
        )


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
