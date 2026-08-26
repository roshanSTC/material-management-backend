from datetime import datetime

from app.extensions.database import db


class CustomerDeliveryInvoice(db.Model):
    __tablename__ = "customer_delivery_invoices"

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

    invoice_number = db.Column(
        db.String(100),
        nullable=False,
    )

    invoice_date = db.Column(
        db.Date,
        nullable=False,
    )

    gst_rate = db.Column(
        db.Numeric(5, 2),
        nullable=True,
    )

    round_off = db.Column(
        db.Numeric(18, 2),
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
        back_populates="customer_delivery_invoices",
        lazy="select",
    )

    items = db.relationship(
        "CustomerDeliveryInvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerDeliveryInvoice "
            f"{self.id}: {self.invoice_number}>"
        )