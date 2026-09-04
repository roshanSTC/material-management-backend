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

    cost_sheet_item_id = db.Column(
        db.Integer,
        db.ForeignKey("cost_sheet_items.id"),
        nullable=True,
    )

    quotation_number = db.Column(
        db.String(100),
        nullable=True,
    )

    item_code = db.Column(
        db.String(100),
        nullable=True,
    )

    material_name = db.Column(
        db.String(255),
        nullable=False,
    )

    quantity = db.Column(
        db.Numeric(18, 3),
        nullable=False,
    )

    unit_price = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    net_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    customs_duty_rate = db.Column(
        db.Numeric(5, 4),
        nullable=True,
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