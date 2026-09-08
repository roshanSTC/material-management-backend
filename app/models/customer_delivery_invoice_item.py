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

    material_name = db.Column(
        db.String(255),
        nullable=False,
    )

    hsn_code = db.Column(
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

    net_amount = db.Column(
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

    # Property aliases for backward/forward compatibility
    @property
    def material_description(self):
        return self.material_name

    @material_description.setter
    def material_description(self, val):
        self.material_name = val

    @property
    def hsn_sac(self):
        return self.hsn_code

    @hsn_sac.setter
    def hsn_sac(self, val):
        self.hsn_code = val

    @property
    def rate_per_unit(self):
        return self.unit_price

    @rate_per_unit.setter
    def rate_per_unit(self, val):
        self.unit_price = val

    @property
    def amount(self):
        return self.net_amount

    @amount.setter
    def amount(self, val):
        self.net_amount = val

    def __repr__(self) -> str:
        return (
            f"<CustomerDeliveryInvoiceItem "
            f"{self.id}: {self.material_name}>"
        )