from datetime import datetime

from app.extensions.database import db


class SupplierInvoiceItem(db.Model):
    __tablename__ = "supplier_invoice_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    supplier_invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_invoices.id"),
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
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    invoice = db.relationship(
        "SupplierInvoice",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<SupplierInvoiceItem {self.id}>"