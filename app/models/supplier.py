from datetime import datetime

from app.extensions.database import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(255),
        nullable=False,
    )

    nickname = db.Column(
        db.String(100),
        nullable=True,
    )

    email = db.Column(
        db.String(255),
        nullable=True,
    )

    contact_number = db.Column(
        db.String(30),
        nullable=True,
    )

    address = db.Column(
        db.Text,
        nullable=True,
    )

    street = db.Column(
        db.Text,
        nullable=True,
    )

    area = db.Column(
        db.String(255),
        nullable=True,
    )

    city = db.Column(
        db.String(100),
        nullable=True,
    )

    state = db.Column(
        db.String(100),
        nullable=True,
    )

    pincode = db.Column(
        db.String(20),
        nullable=True,
    )

    country = db.Column(
        db.String(100),
        nullable=True,
    )

    website_url = db.Column(
        db.String(2048),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    pocs = db.relationship(
        "SupplierPoc",
        back_populates="supplier",
        cascade="all, delete-orphan",
        lazy="select",
    )

    projects = db.relationship(
        "Project",
        back_populates="supplier",
        lazy="select",
    )

    quotation_requests = db.relationship(
        "QuotationRequest",
        back_populates="supplier",
        lazy="select",
    )

    supplier_quotations = db.relationship(
        "SupplierQuotation",
        back_populates="supplier",
        lazy="select",
    )

    supplier_order_confirmations = db.relationship(
        "SupplierOrderConfirmation",
        back_populates="supplier",
        lazy="select",
    )

    supplier_payments = db.relationship(
        "SupplierPayment",
        back_populates="supplier",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Supplier {self.id}: {self.name}>"