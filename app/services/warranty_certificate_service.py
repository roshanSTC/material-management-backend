from app.extensions.database import db
from app.models import WarrantyCertificate
from app.repositories.warranty_certificate_repository import (
    create_warranty_certificate,
    delete_warranty_certificate,
    get_project,
    get_warranty_certificate,
    list_warranty_certificates,
    update_warranty_certificate,
)


class WarrantyCertificateError(Exception):
    pass


class ProjectNotFoundError(WarrantyCertificateError):
    pass


class WarrantyCertificateNotFoundError(WarrantyCertificateError):
    pass


def create_warranty_certificate_transaction(*, data: dict) -> WarrantyCertificate:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    cert = create_warranty_certificate(data=data)
    db.session.flush()

    return cert


def get_warranty_certificate_record(warranty_certificate_id: int) -> WarrantyCertificate:
    cert = get_warranty_certificate(warranty_certificate_id)
    if cert is None:
        raise WarrantyCertificateNotFoundError(
            f"Warranty certificate with ID {warranty_certificate_id} not found."
        )
    return cert


def list_warranty_certificate_records(
    *,
    project_id: int | None = None,
    po_no: str | None = None,
    invoice_no: str | None = None,
) -> list[WarrantyCertificate]:
    return list_warranty_certificates(
        project_id=project_id,
        po_no=po_no,
        invoice_no=invoice_no,
    )


def update_warranty_certificate_transaction(
    *,
    warranty_certificate_id: int,
    data: dict,
) -> WarrantyCertificate:
    cert = get_warranty_certificate(warranty_certificate_id)
    if cert is None:
        raise WarrantyCertificateNotFoundError(
            f"Warranty certificate with ID {warranty_certificate_id} not found."
        )

    if "project_id" in data:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    updated_cert = update_warranty_certificate(
        cert=cert,
        data=data,
    )
    db.session.flush()

    return updated_cert


def delete_warranty_certificate_transaction(warranty_certificate_id: int) -> list[str]:
    cert = get_warranty_certificate(warranty_certificate_id)
    if cert is None:
        raise WarrantyCertificateNotFoundError(
            f"Warranty certificate with ID {warranty_certificate_id} not found."
        )

    storage_keys = delete_warranty_certificate(warranty_certificate_id)
    db.session.flush()
    return storage_keys
