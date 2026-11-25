from datetime import datetime

from app.extensions.database import db


class CustomerDeliveryInvoiceItem(db.Model):
    __tablename__ = "customer_delivery_invoice_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_delivery_invoices.id"),
        nullable=False,
        index=True,
    )

    sr_no = db.Column(
        db.Integer,
        nullable=True,
    )

    description = db.Column(
        db.String(500),
        nullable=False,
    )

    hsn_sac = db.Column(
        db.String(50),
        nullable=True,
    )

    quantity = db.Column(
        db.Numeric(18, 3),
        nullable=False,
    )

    unit_price = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    total_amount = db.Column(
        db.Numeric(18, 2),
        nullable=False,
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

    invoice = db.relationship(
        "CustomerDeliveryInvoice",
        back_populates="items",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerDeliveryInvoiceItem "
            f"{self.id}: {self.description}>"
        )