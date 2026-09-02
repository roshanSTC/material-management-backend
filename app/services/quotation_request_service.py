from flask_jwt_extended import get_jwt_identity

from app.extensions.database import db
from app.models import QuotationRequest

from app.models.quotation_request_item import QuotationRequestItem
from app.repositories.quotation_request_repository import (
    create_quotation_request,
    get_project,
    get_quotation_request,
    get_supplier,
    list_quotation_requests,
)


from app.services.attachment_service import (
    create_attachment,
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
    quotation_requested_date,
    supplier_contacted: bool,
    remarks: str | None,
    items: list[dict],
    files=None,
) -> QuotationRequest:

    project = get_project(project_id)

    if project is None:
        raise ProjectNotFoundError(
            f"Project with id {project_id} was not found."
        )

    supplier = get_supplier(supplier_id)

    if supplier is None:
        raise SupplierNotFoundError(
            f"Supplier with id {supplier_id} was not found."
        )

    if project.supplier_id != supplier.id:
        raise SupplierProjectMismatchError(
            "The selected supplier does not belong "
            "to the selected project."
        )

    quotation_request = create_quotation_request(
        project_id=project_id,
        supplier_id=supplier_id,
        quotation_requested_date=quotation_requested_date,
        supplier_contacted=supplier_contacted,
        remarks=remarks,
        items=items,
    )

    db.session.flush()

    # -----------------------------------------
    # Attachments
    # -----------------------------------------

    if files:
        for file in files:

            if not file or not file.filename:
                continue

            create_attachment(
                file=file,
                entity_type="quotation_request",
                entity_id=quotation_request.id,
                uploaded_by=int(get_jwt_identity()),
            )

    db.session.commit()

    return quotation_request



def update_quotation_request_transaction(
    quotation_request_id,
    project_id=None,
    supplier_id=None,
    quotation_requested_date=None,
    supplier_contacted=None,
    remarks=None,
    items=None,
):
    quotation_request = (
        db.session.get(
            QuotationRequest,
            quotation_request_id,
        )
    )

    if not quotation_request:
        raise QuotationRequestNotFoundError(
            "Quotation request not found."
        )

    # Only validate project if it is being changed
    if project_id is not None:

        project = get_project(project_id)

        if not project:
            raise ProjectNotFoundError(
                "Project not found."
            )

        quotation_request.project_id = project_id

    # Only validate supplier if it is being changed
    if supplier_id is not None:

        supplier = get_supplier(supplier_id)

        if not supplier:
            raise SupplierNotFoundError(
                "Supplier not found."
            )

        # Validate supplier belongs to project
        final_project_id = (
            project_id
            if project_id is not None
            else quotation_request.project_id
        )

        if supplier.project_id != final_project_id:
            raise SupplierProjectMismatchError(
                "Supplier does not belong to the selected project."
            )

        quotation_request.supplier_id = supplier_id

    # Update scalar fields only when supplied
    if quotation_requested_date is not None:
        quotation_request.quotation_requested_date = (
            quotation_requested_date
        )

    if supplier_contacted is not None:
        quotation_request.supplier_contacted = (
            supplier_contacted
        )

    if remarks is not None:
        quotation_request.remarks = remarks

    # Replace items only when items are supplied
    if items is not None:

        for item in list(quotation_request.items):
            db.session.delete(item)

        db.session.flush()

        for item_data in items:

            item = QuotationRequestItem(
                quotation_request_id=quotation_request.id,
                material_name=item_data["material_name"],
                quantity=item_data["quantity"],
            )

            db.session.add(item)

    db.session.flush()

    return quotation_request



def delete_quotation_request_transaction(quotation_request_id: int):
    quotation_request = get_quotation_request_record(
        quotation_request_id
    )

    if not quotation_request:
        raise QuotationRequestNotFoundError(
            f"Quotation request {quotation_request_id} not found."
        )

    db.session.delete(quotation_request)

    db.session.flush()

    return quotation_request