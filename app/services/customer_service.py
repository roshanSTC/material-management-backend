from app.extensions.database import db
from app.models import Customer, CustomerPoc


class CustomerNotFoundError(Exception):
    """Raised when a customer does not exist."""


def _format_address(
    street: str | None = None,
    area: str | None = None,
    city: str | None = None,
    state: str | None = None,
    pincode: str | None = None,
    country: str | None = None,
) -> str | None:
    parts = []
    if street and street.strip():
        parts.append(street.strip())
    if area and area.strip():
        parts.append(area.strip())
    if city and city.strip():
        parts.append(city.strip())

    state_pin = []
    if state and state.strip():
        state_pin.append(state.strip())
    if pincode and pincode.strip():
        state_pin.append(pincode.strip())
    if state_pin:
        parts.append(" ".join(state_pin))

    if country and country.strip():
        parts.append(country.strip())

    return ", ".join(parts) if parts else None


def create_customer(
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
    address: str | None = None,
    website_url: str | None = None,
) -> Customer:
    # If address not provided, compute from segregated fields
    if not address or not address.strip():
        address = _format_address(street, area, city, state, pincode, country)
    elif address:
        address = address.strip()

    # If email/contact_number not provided at top level, sync from first POC if available
    if (not email or not email.strip()) and pocs:
        first_poc_email = pocs[0].get("email")
        if first_poc_email:
            email = first_poc_email.strip()

    if (not contact_number or not contact_number.strip()) and pocs:
        first_poc_contact = pocs[0].get("contact_number")
        if first_poc_contact:
            contact_number = first_poc_contact.strip()

    customer = Customer(
        name=name.strip(),
        nickname=nickname.strip() if nickname else None,
        email=email.strip() if email else None,
        contact_number=contact_number.strip() if contact_number else None,
        address=address,
        street=street.strip() if street else None,
        area=area.strip() if area else None,
        city=city.strip() if city else None,
        state=state.strip() if state else None,
        pincode=pincode.strip() if pincode else None,
        country=country.strip() if country else None,
        website_url=website_url.strip() if website_url else None,
    )

    if pocs:
        for poc_data in pocs:
            poc = CustomerPoc(
                name=poc_data["name"].strip(),
                email=poc_data.get("email", "").strip() if poc_data.get("email") else None,
                contact_number=poc_data.get("contact_number", "").strip() if poc_data.get("contact_number") else None,
                designation=poc_data.get("designation", "").strip() if poc_data.get("designation") else None,
            )
            customer.pocs.append(poc)

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
    address: str | None = None,
    website_url: str | None = None,
) -> Customer:
    customer = get_customer(customer_id)

    if name is not None:
        customer.name = name.strip()

    if nickname is not None:
        customer.nickname = nickname.strip() if nickname else None

    if street is not None:
        customer.street = street.strip() if street else None

    if area is not None:
        customer.area = area.strip() if area else None

    if city is not None:
        customer.city = city.strip() if city else None

    if state is not None:
        customer.state = state.strip() if state else None

    if pincode is not None:
        customer.pincode = pincode.strip() if pincode else None

    if country is not None:
        customer.country = country.strip() if country else None

    if address is not None:
        customer.address = address.strip() if address else None
    elif any(x is not None for x in (street, area, city, state, pincode, country)):
        customer.address = _format_address(
            customer.street,
            customer.area,
            customer.city,
            customer.state,
            customer.pincode,
            customer.country,
        )

    if email is not None:
        customer.email = email.strip() if email else None

    if contact_number is not None:
        customer.contact_number = contact_number.strip() if contact_number else None

    if website_url is not None:
        customer.website_url = website_url.strip() if website_url else None

    if pocs is not None:
        customer.pocs.clear()
        for poc_data in pocs:
            poc = CustomerPoc(
                name=poc_data["name"].strip(),
                email=poc_data.get("email", "").strip() if poc_data.get("email") else None,
                contact_number=poc_data.get("contact_number", "").strip() if poc_data.get("contact_number") else None,
                designation=poc_data.get("designation", "").strip() if poc_data.get("designation") else None,
            )
            customer.pocs.append(poc)

        if not customer.email and customer.pocs:
            customer.email = customer.pocs[0].email
        if not customer.contact_number and customer.pocs:
            customer.contact_number = customer.pocs[0].contact_number

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
