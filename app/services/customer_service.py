from app.extensions.database import db
from app.models import Customer


class CustomerNotFoundError(Exception):
    """Raised when a customer does not exist."""


def create_customer(
    *,
    name: str,
    email: str,
    contact_number: str,
    address: str,
    website_url: str | None = None,
) -> Customer:
    customer = Customer(
        name=name.strip(),
        email=email.strip(),
        contact_number=contact_number.strip(),
        address=address.strip(),
        website_url=website_url.strip() if website_url else None,
    )

    db.session.add(customer)
    db.session.commit()

    return customer


def get_customer(customer_id: int) -> Customer:
    customer = db.session.get(Customer, customer_id)

    if customer is None:
        raise CustomerNotFoundError(
            f"Customer with id {customer_id} was not found."
        )

    return customer


def list_customers() -> list[Customer]:
    return db.session.execute(
        db.select(Customer)
        .order_by(Customer.id.desc())
    ).scalars().all()


def update_customer(
    customer_id: int,
    *,
    name: str | None = None,
    email: str | None = None,
    contact_number: str | None = None,
    address: str | None = None,
    website_url: str | None = None,
) -> Customer:
    customer = get_customer(customer_id)

    if name is not None:
        customer.name = name.strip()

    if email is not None:
        customer.email = email.strip()

    if contact_number is not None:
        customer.contact_number = contact_number.strip()

    if address is not None:
        customer.address = address.strip()

    if website_url is not None:
        customer.website_url = website_url.strip()

    db.session.commit()

    return customer


def delete_customer(customer_id: int) -> list[str]:
    customer = get_customer(customer_id)
    all_storage_keys = []

    from app.models.project import Project
    from app.models.customer_query import CustomerQuery
    from app.models.customer_quotation import CustomerQuotation
    from app.models.customer_tender import CustomerTender
    from app.models.purchase_order import PurchaseOrder

    db.session.execute(
        db.update(Project)
        .where(Project.customer_id == customer_id)
        .values(customer_id=None)
    )
    db.session.execute(
        db.update(CustomerQuery)
        .where(CustomerQuery.customer_id == customer_id)
        .values(customer_id=None)
    )
    db.session.execute(
        db.update(CustomerQuotation)
        .where(CustomerQuotation.customer_id == customer_id)
        .values(customer_id=None)
    )
    db.session.execute(
        db.update(CustomerTender)
        .where(CustomerTender.customer_id == customer_id)
        .values(customer_id=None)
    )
    db.session.execute(
        db.update(PurchaseOrder)
        .where(PurchaseOrder.customer_id == customer_id)
        .values(customer_id=None)
    )

    from app.models.attachment import Attachment
    attachments = db.session.execute(
        db.select(Attachment).where(
            Attachment.entity_type == "customer",
            Attachment.entity_id == customer_id,
        )
    ).scalars().all()
    for att in attachments:
        if att.storage_key:
            all_storage_keys.append(att.storage_key)
        db.session.delete(att)

    db.session.delete(customer)
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
