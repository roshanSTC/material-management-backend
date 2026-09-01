from app.extensions.database import db
from app.models import QuotationRequest

from app.repositories.quotation_request_repository import (
    create_quotation_request,
    get_project,
    get_quotation_request,
    get_supplier,
    list_quotation_requests,
)


class QuotationRequestError(Exception):
    """Base error for quotation request operations."""


class ProjectNotFoundError(QuotationRequestError):
    """Raised when the project does not exist."""


class SupplierNotFoundError(QuotationRequestError):
    """Raised when the supplier does not exist."""


class SupplierProjectMismatchError(
    QuotationRequestError
):
    """Raised when supplier does not belong to project."""


class QuotationRequestNotFoundError(
    QuotationRequestError
):
    """Raised when quotation request does not exist."""


def list_quotation_request_records() -> list[QuotationRequest]:

    return list_quotation_requests()


def get_quotation_request_record(
    quotation_request_id: int,
) -> QuotationRequest:

    quotation_request = get_quotation_request(
        quotation_request_id
    )

    if quotation_request is None:
        raise QuotationRequestNotFoundError(
            f"Quotation Request with id "
            f"{quotation_request_id} was not found."
        )

    return quotation_request


def create_quotation_request_transaction(
    *,
    project_id: int,
    supplier_id: int,
    request_date,
    remarks: str | None,
    items: list[dict],
) -> QuotationRequest:

    project = get_project(
        project_id
    )

    if project is None:
        raise ProjectNotFoundError(
            f"Project with id "
            f"{project_id} was not found."
        )

    supplier = get_supplier(
        supplier_id
    )

    if supplier is None:
        raise SupplierNotFoundError(
            f"Supplier with id "
            f"{supplier_id} was not found."
        )

    if project.supplier_id != supplier.id:
        raise SupplierProjectMismatchError(
            "The selected supplier does not "
            "belong to the selected project."
        )

    quotation_request = create_quotation_request(
        project_id=project_id,
        supplier_id=supplier_id,
        request_date=request_date,
        remarks=remarks,
        items=items,
    )

    db.session.flush()

    return quotation_request