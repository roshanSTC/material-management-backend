from app.extensions.database import db
from app.models import (
    Project,
    QuotationRequest,
    QuotationRequestItem,
    Supplier,
)


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


def create_quotation_request(
    *,
    project_id: int,
    supplier_id: int,
    quotation_requested_date,
    supplier_contacted: bool,
    remarks: str | None,
    items: list[dict],
) -> QuotationRequest:

    quotation_request = QuotationRequest(
        project_id=project_id,
        supplier_id=supplier_id,
        quotation_requested_date=quotation_requested_date,
        supplier_contacted=supplier_contacted,
        remarks=remarks.strip() if remarks else None,
    )

    for item_data in items:
        item = QuotationRequestItem(
            material_name=item_data["material_name"].strip(),
            quantity=item_data["quantity"],
        )

        quotation_request.items.append(item)

    db.session.add(quotation_request)

    return quotation_request


def get_quotation_request(
    quotation_request_id: int,
) -> QuotationRequest | None:

    return db.session.get(
        QuotationRequest,
        quotation_request_id,
    )


def list_quotation_requests(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
) -> list[QuotationRequest]:
    statement = db.select(QuotationRequest)
    if project_id is not None:
        statement = statement.where(QuotationRequest.project_id == project_id)
    if supplier_id is not None:
        statement = statement.where(QuotationRequest.supplier_id == supplier_id)

    return db.session.execute(
        statement.order_by(QuotationRequest.id.desc())
    ).scalars().all()