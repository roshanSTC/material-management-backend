from app.extensions.database import db
from app.models import Supplier


class SupplierNotFoundError(Exception):
    """Raised when a supplier does not exist."""


def create_supplier(
    *,
    name: str,
    email: str,
    contact_number: str,
    address: str,
    website_url: str | None = None,
) -> Supplier:
    supplier = Supplier(
        name=name.strip(),
        email=email.strip(),
        contact_number=contact_number.strip(),
        address=address.strip(),
        website_url=website_url.strip() if website_url else None,
    )

    db.session.add(supplier)
    db.session.commit()

    return supplier


def get_supplier(supplier_id: int) -> Supplier:
    supplier = db.session.get(Supplier, supplier_id)

    if supplier is None:
        raise SupplierNotFoundError(
            f"Supplier with id {supplier_id} was not found."
        )

    return supplier


def list_suppliers() -> list[Supplier]:
    return db.session.execute(
        db.select(Supplier)
        .order_by(Supplier.id.desc())
    ).scalars().all()


def update_supplier(
    supplier_id: int,
    *,
    name: str | None = None,
    email: str | None = None,
    contact_number: str | None = None,
    address: str | None = None,
    website_url: str | None = None,
) -> Supplier:
    supplier = get_supplier(supplier_id)

    if name is not None:
        supplier.name = name.strip()

    if email is not None:
        supplier.email = email.strip()

    if contact_number is not None:
        supplier.contact_number = contact_number.strip()

    if address is not None:
        supplier.address = address.strip()

    if website_url is not None:
        supplier.website_url = website_url.strip()

    db.session.commit()

    return supplier


def delete_supplier(supplier_id: int) -> list[str]:
    supplier = get_supplier(supplier_id)
    all_storage_keys = []

    from app.models.project import Project
    from app.models.quotation_request import QuotationRequest
    from app.models.supplier_quotation import SupplierQuotation
    from app.models.supplier_order_confirmation import SupplierOrderConfirmation
    from app.models.supplier_proforma_invoice import SupplierProformaInvoice
    from app.models.supplier_invoice import SupplierInvoice
    from app.models.supplier_packing_list import SupplierPackingList
    from app.models.import_logistics import ImportLogistics
    from app.models.supplier_payment import SupplierPayment

    db.session.execute(
        db.update(Project)
        .where(Project.supplier_id == supplier_id)
        .values(supplier_id=None)
    )
    db.session.execute(
        db.update(QuotationRequest)
        .where(QuotationRequest.supplier_id == supplier_id)
        .values(supplier_id=None)
    )
    db.session.execute(
        db.update(SupplierQuotation)
        .where(SupplierQuotation.supplier_id == supplier_id)
        .values(supplier_id=None)
    )
    db.session.execute(
        db.update(SupplierOrderConfirmation)
        .where(SupplierOrderConfirmation.supplier_id == supplier_id)
        .values(supplier_id=None)
    )
    db.session.execute(
        db.update(SupplierProformaInvoice)
        .where(SupplierProformaInvoice.supplier_id == supplier_id)
        .values(supplier_id=None)
    )
    db.session.execute(
        db.update(SupplierInvoice)
        .where(SupplierInvoice.supplier_id == supplier_id)
        .values(supplier_id=None)
    )
    db.session.execute(
        db.update(SupplierPackingList)
        .where(SupplierPackingList.supplier_id == supplier_id)
        .values(supplier_id=None)
    )
    db.session.execute(
        db.update(ImportLogistics)
        .where(ImportLogistics.supplier_id == supplier_id)
        .values(supplier_id=None)
    )
    db.session.execute(
        db.update(SupplierPayment)
        .where(SupplierPayment.supplier_id == supplier_id)
        .values(supplier_id=None)
    )

    from app.models.attachment import Attachment
    attachments = db.session.execute(
        db.select(Attachment).where(
            Attachment.entity_type == "supplier",
            Attachment.entity_id == supplier_id,
        )
    ).scalars().all()
    for att in attachments:
        if att.storage_key:
            all_storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(supplier)
    db.session.commit()

    try:
        from app.extensions.storage import get_storage
        storage = get_storage()
        for key in all_storage_keys:
            try:
                if storage.exists(key):
                    storage.delete(key)
            except Exception:
                pass
    except Exception:
        pass

    return all_storage_keys
