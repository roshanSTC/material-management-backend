from app.extensions.database import db
from app.models import (
    Project,
    QuotationRequest,
    QuotationRequestItem,
    Supplier,
)
from app.utils.remark_utils import normalize_remark_for_db


def get_project(project_id: int) -> Project | None:
    return db.session.get(Project, project_id)


def get_supplier(supplier_id: int) -> Supplier | None:
    return db.session.get(Supplier, supplier_id)


def create_quotation_request(
    *,
    project_id: int,
    supplier_id: int | None = None,
    supplier_name: str | None = None,
    request_date,
    supplier_contacted: bool = False,
    remarks: str | None = None,
    items: list[dict] = (),
) -> QuotationRequest:

    quotation_request = QuotationRequest(
        project_id=project_id,
        supplier_id=supplier_id,
        supplier_name=supplier_name.strip() if isinstance(supplier_name, str) and supplier_name.strip() else None,
        request_date=request_date,
        supplier_contacted=supplier_contacted,
        remarks=normalize_remark_for_db(remarks),
    )

    for idx, item_data in enumerate(items, start=1):
        item = QuotationRequestItem(
            sr_no=item_data.get("sr_no") if item_data.get("sr_no") is not None else idx,
            description=str(item_data["description"]).strip(),
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


def get_latest_quotation_request(project_id: int) -> QuotationRequest | None:
    statement = (
        db.select(QuotationRequest)
        .where(QuotationRequest.project_id == project_id)
        .order_by(QuotationRequest.id.desc())
    )
    return db.session.execute(statement).scalars().first()


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