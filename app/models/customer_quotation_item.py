from datetime import datetime

from app.extensions.database import db


class CustomerQuotationItem(db.Model):
    __tablename__ = "customer_quotation_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    customer_quotation_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_quotations.id"),
        nullable=False,
        index=True,
    )

    material_name = db.Column(
        db.String(255),
        nullable=False,
    )

    unit_price = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    quantity = db.Column(
        db.Numeric(18, 3),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    customer_quotation = db.relationship(
        "CustomerQuotation",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<CustomerQuotationItem {self.id}>"