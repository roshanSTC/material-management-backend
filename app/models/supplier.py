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

    email = db.Column(
        db.String(255),
        nullable=False,
    )

    contact_number = db.Column(
        db.String(30),
        nullable=False,
    )

    address = db.Column(
        db.Text,
        nullable=False,
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