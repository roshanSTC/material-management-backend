
from app.extensions.database import db
from app.models import Customer, Project, Supplier
from app.repositories.project_repository import (
    create_project as repository_create_project,
    get_project as repository_get_project,
    list_projects as repository_list_projects,
    update_project as repository_update_project,
)


class ProjectNotFoundError(Exception):
    """Raised when a project does not exist."""


class CustomerNotFoundError(Exception):
    """Raised when the referenced customer does not exist."""


class SupplierNotFoundError(Exception):
    """Raised when the referenced supplier does not exist."""


def _validate_customer(customer_id: int) -> None:
    customer = db.session.get(Customer, customer_id)

    if customer is None:
        raise CustomerNotFoundError(
            f"Customer with id {customer_id} was not found."
        )


def _validate_supplier(supplier_id: int) -> None:
    supplier = db.session.get(Supplier, supplier_id)

    if supplier is None:
        raise SupplierNotFoundError(
            f"Supplier with id {supplier_id} was not found."
        )


def create_project(
    *,
    project_title: str,
    customer_id: int,
    supplier_id: int,
) -> Project:
    _validate_customer(customer_id)
    _validate_supplier(supplier_id)

    project = repository_create_project(
        project_title=project_title.strip(),
        customer_id=customer_id,
        supplier_id=supplier_id,
    )

    db.session.commit()

    return project


def get_project(project_id: int) -> Project:
    project = repository_get_project(project_id)

    if project is None:
        raise ProjectNotFoundError(
            f"Project with id {project_id} was not found."
        )

    return project


def list_projects() -> list[Project]:
    return repository_list_projects()


def update_project(
    project_id: int,
    *,
    project_title: str | None = None,
    customer_id: int | None = None,
    supplier_id: int | None = None,
) -> Project:
    project = get_project(project_id)

    if project_title is not None:
        project.project_title = project_title.strip()

    if customer_id is not None:
        _validate_customer(customer_id)
        project.customer_id = customer_id

    if supplier_id is not None:
        _validate_supplier(supplier_id)
        project.supplier_id = supplier_id

    project = repository_update_project(project)

    db.session.commit()

    return project


def delete_project(project_id: int) -> list[str]:
    project = get_project(project_id)
    storage_keys = []

    from app.models.attachment import Attachment

    step_entities = [
        ("customer_query", [cq.id for cq in project.customer_queries]),
        ("quotation_request", [qr.id for qr in project.quotation_requests]),
        ("supplier_quotation", [sq.id for sq in project.supplier_quotations]),
        ("customer_quotation", [cq.id for cq in project.customer_quotations]),
        ("customer_tender", [ct.id for ct in project.customer_tenders]),
        ("bid_submission", [bs.id for bs in project.bid_submissions]),
        ("purchase_order", [po.id for po in project.purchase_orders]),
        ("order_confirmation", [soc.id for soc in project.supplier_order_confirmations]),
        ("supplier_order_confirmation", [soc.id for soc in project.supplier_order_confirmations]),
        ("supplier_proforma_invoice", [spi.id for spi in project.supplier_proforma_invoices]),
        ("proforma_invoice", [spi.id for spi in project.supplier_proforma_invoices]),
        ("supplier_invoice", [si.id for si in project.supplier_invoices]),
        ("supplier_packing_list", [spl.id for spl in project.supplier_packing_lists]),
        ("import_logistics", [il.id for il in project.import_logistics]),
        ("bill_of_entry", [boe.id for boe in project.bills_of_entry]),
        ("customs_clearance", [cc.id for cc in project.customs_clearances]),
        ("customer_delivery_invoice", [cdi.id for cdi in project.customer_delivery_invoices]),
        ("customer_delivery_packing_list", [cdpl.id for cdpl in project.customer_delivery_packing_lists]),
        ("delivery_challan", [dc.id for dc in project.delivery_challans]),
        ("warranty_certificate", [wc.id for wc in project.warranty_certificates]),
        ("transport_detail", [td.id for td in project.transport_details]),
        ("customer_payment", [cp.id for cp in project.customer_payments]),
        ("supplier_payment", [sp.id for sp in project.supplier_payments]),
        ("project", [project.id]),
    ]

    for entity_type, ids in step_entities:
        if ids:
            attachments = db.session.execute(
                db.select(Attachment).where(
                    Attachment.entity_type == entity_type,
                    Attachment.entity_id.in_(ids),
                )
            ).scalars().all()
            for att in attachments:
                if att.storage_key:
                    storage_keys.append(att.storage_key)
                db.session.delete(att)

    db.session.delete(project)
    db.session.commit()

    try:
        from app.extensions.storage import get_storage
        storage = get_storage()
        for key in storage_keys:
            try:
                if storage.exists(key):
                    storage.delete(key)
            except Exception:
                pass
    except Exception:
        pass

    return storage_keys


