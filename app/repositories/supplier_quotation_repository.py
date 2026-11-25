from sqlalchemy.orm import selectinload

from app.extensions.database import db
from app.models import Project, Supplier, SupplierQuotation, SupplierQuotationItem


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


def create_supplier_quotation(*, data: dict) -> SupplierQuotation:
    currency_unit = data.get("currency_unit") or data.get("value_symbol") or data.get("currency")
    currency = data.get("currency") or currency_unit
    currency_symbol = data.get("currency_symbol") or (currency_unit if currency_unit in ("₹", "$", "€", "£") else ("₹" if currency == "INR" else None))
    total_net_amount = data.get("total_net_amount") if data.get("total_net_amount") is not None else data.get("quotation_value")
    total_gross_amount = data.get("total_gross_amount") if data.get("total_gross_amount") is not None else data.get("quotation_value")
    total_amount = data.get("total_amount") if data.get("total_amount") is not None else (total_gross_amount or total_net_amount)

    supplier_quotation = SupplierQuotation(
        project_id=data["project_id"],
        supplier_id=data.get("supplier_id"),
        supplier_name=_normalize_optional_string(data.get("supplier_name")),
        quotation_no=data["quotation_no"].strip(),
        quotation_date=data["quotation_date"],
        quotation_value=data["quotation_value"],
        currency_unit=_normalize_optional_string(currency_unit),
        currency_symbol=_normalize_optional_string(currency_symbol),
        currency=_normalize_optional_string(currency),
        total_net_amount=total_net_amount,
        total_gross_amount=total_gross_amount,
        total_amount=total_amount,
        status=_normalize_optional_string(data.get("status")) or "completed",
        quotation_validity=_normalize_optional_string(data.get("quotation_validity")),
        incoterms=_normalize_optional_string(data.get("incoterms")),
        payment_terms=_normalize_optional_string(data.get("payment_terms")),
        delivery_period=_normalize_optional_string(data.get("delivery_period")),
        warranty_period=_normalize_optional_string(data.get("warranty_period")),
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


def get_latest_supplier_quotation_for_project(
    project_id: int,
) -> SupplierQuotation | None:
    return db.session.execute(
        db.select(SupplierQuotation)
        .options(selectinload(SupplierQuotation.items))
        .where(SupplierQuotation.project_id == project_id)
        .order_by(SupplierQuotation.id.desc())
    ).scalars().first()



def update_supplier_quotation(
    supplier_quotation: SupplierQuotation,
    *,
    data: dict,
) -> SupplierQuotation:
    string_fields = {
        "quotation_no",
        "supplier_name",
        "currency_unit",
        "currency_symbol",
        "currency",
        "status",
        "quotation_validity",
        "incoterms",
        "payment_terms",
        "delivery_period",
        "warranty_period",
        "remark",
    }
    scalar_fields = {
        "project_id",
        "supplier_id",
        "quotation_date",
        "quotation_value",
        "total_net_amount",
        "total_gross_amount",
        "total_amount",
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
    for idx, item_data in enumerate(items):
        quantity = item_data["quantity"]
        unit_price = item_data.get("unit_price")
        total_amount = item_data.get("total_amount")
        sr_no = item_data.get("sr_no") if item_data.get("sr_no") is not None else (idx + 1)
        description = str(item_data["description"]).strip()
        hsn_sac = _normalize_optional_string(item_data.get("hsn_sac"))
        if total_amount is None and unit_price is not None and quantity is not None:
            try:
                total_amount = quantity * unit_price
            except Exception:
                pass

        supplier_quotation.items.append(
            SupplierQuotationItem(
                sr_no=sr_no,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                total_amount=total_amount,
                hsn_sac=hsn_sac,
            )
        )


from app.utils.remark_utils import normalize_remark_for_db


def _normalize_optional_string(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return normalize_remark_for_db(value)
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return str(value)
