from app.extensions.database import db
from app.models import Supplier, SupplierPoc


class SupplierNotFoundError(Exception):
    """Raised when a supplier does not exist."""


def create_supplier(
    *,
    name: str,
    nickname: str | None = None,
    street: str | None = None,
    area: str | None = None,
    city: str | None = None,
    state: str | None = None,
    pincode: str | None = None,
    country: str | None = None,
    pocs: list[dict] | None = None,
    email: str | None = None,
    contact_number: str | None = None,
) -> Supplier:
    # If email/contact_number not provided at top level, sync from first POC if available
    if (not email or not email.strip()) and pocs:
        first_poc_email = pocs[0].get("email")
        if first_poc_email:
            email = first_poc_email.strip()

    if (not contact_number or not contact_number.strip()) and pocs:
        first_poc_contact = pocs[0].get("contact_number")
        if first_poc_contact:
            contact_number = first_poc_contact.strip()

    supplier = Supplier(
        name=name.strip(),
        nickname=nickname.strip() if nickname else None,
        email=email.strip() if email else None,
        contact_number=contact_number.strip() if contact_number else None,
        street=street.strip() if street else None,
        area=area.strip() if area else None,
        city=city.strip() if city else None,
        state=state.strip() if state else None,
        pincode=pincode.strip() if pincode else None,
        country=country.strip() if country else None,
    )

    if pocs:
        for poc_data in pocs:
            poc = SupplierPoc(
                name=poc_data["name"].strip(),
                email=poc_data.get("email", "").strip() if poc_data.get("email") else None,
                contact_number=poc_data.get("contact_number", "").strip() if poc_data.get("contact_number") else None,
                designation=poc_data.get("designation", "").strip() if poc_data.get("designation") else None,
            )
            supplier.pocs.append(poc)

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
    nickname: str | None = None,
    street: str | None = None,
    area: str | None = None,
    city: str | None = None,
    state: str | None = None,
    pincode: str | None = None,
    country: str | None = None,
    pocs: list[dict] | None = None,
    email: str | None = None,
    contact_number: str | None = None,
) -> Supplier:
    supplier = get_supplier(supplier_id)

    if name is not None:
        supplier.name = name.strip()

    if nickname is not None:
        supplier.nickname = nickname.strip() if nickname else None

    if street is not None:
        supplier.street = street.strip() if street else None

    if area is not None:
        supplier.area = area.strip() if area else None

    if city is not None:
        supplier.city = city.strip() if city else None

    if state is not None:
        supplier.state = state.strip() if state else None

    if pincode is not None:
        supplier.pincode = pincode.strip() if pincode else None

    if country is not None:
        supplier.country = country.strip() if country else None

    if email is not None:
        supplier.email = email.strip() if email else None

    if contact_number is not None:
        supplier.contact_number = contact_number.strip() if contact_number else None

    if pocs is not None:
        supplier.pocs.clear()
        for poc_data in pocs:
            poc = SupplierPoc(
                name=poc_data["name"].strip(),
                email=poc_data.get("email", "").strip() if poc_data.get("email") else None,
                contact_number=poc_data.get("contact_number", "").strip() if poc_data.get("contact_number") else None,
                designation=poc_data.get("designation", "").strip() if poc_data.get("designation") else None,
            )
            supplier.pocs.append(poc)

        if not supplier.email and supplier.pocs:
            supplier.email = supplier.pocs[0].email
        if not supplier.contact_number and supplier.pocs:
            supplier.contact_number = supplier.pocs[0].contact_number

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
