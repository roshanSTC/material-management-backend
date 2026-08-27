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