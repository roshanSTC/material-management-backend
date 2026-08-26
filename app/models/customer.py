from datetime import datetime

from app.extensions.database import db


class Customer(db.Model):
    __tablename__ = "customers"

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
    
    customer_queries = db.relationship(
        "CustomerQuery",
        back_populates="customer",
        lazy="select",
    )
    
    customer_quotations = db.relationship(
        "CustomerQuotation",
        back_populates="customer",
        lazy="select",
    )
    
    projects = db.relationship(
        "Project",
        back_populates="customer",
        lazy="select",
    )
    
    purchase_orders = db.relationship(
        "PurchaseOrder",
        back_populates="customer",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Customer {self.id}: {self.name}>"