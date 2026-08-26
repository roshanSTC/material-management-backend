from datetime import datetime

from app.extensions.database import db


class SupplierOrderConfirmation(db.Model):
    __tablename__ = "supplier_order_confirmations"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    purchase_order_id = db.Column(
        db.Integer,
        db.ForeignKey("purchase_orders.id"),
        nullable=True,
        index=True,
    )

    confirmation_date = db.Column(
        db.Date,
        nullable=False,
    )

    email = db.Column(
        db.String(255),
        nullable=True,
    )

    reference_number = db.Column(
        db.String(100),
        nullable=False,
    )

    currency = db.Column(
        db.String(10),
        nullable=False,
    )

    shipping_term = db.Column(
        db.String(100),
        nullable=True,
    )

    delivery_term = db.Column(
        db.String(100),
        nullable=True,
    )

    payment_terms = db.Column(
        db.String(255),
        nullable=True,
    )

    warranty_period = db.Column(
        db.String(100),
        nullable=True,
    )

    remark = db.Column(
        db.Text,
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

    project = db.relationship(
        "Project",
        back_populates="supplier_order_confirmations",
    )

    supplier = db.relationship(
        "Supplier",
        back_populates="supplier_order_confirmations",
    )

    purchase_order = db.relationship(
        "PurchaseOrder",
        back_populates="supplier_order_confirmations",
    )

    items = db.relationship(
        "SupplierOrderConfirmationItem",
        back_populates="supplier_order_confirmation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<SupplierOrderConfirmation {self.id}>"