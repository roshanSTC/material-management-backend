from datetime import datetime

from app.extensions.database import db


class SupplierOrderConfirmationItem(db.Model):
    __tablename__ = "supplier_order_confirmation_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    supplier_order_confirmation_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_order_confirmations.id"),
        nullable=False,
        index=True,
    )

    item_description = db.Column(
        db.String(500),
        nullable=False,
    )

    hsn = db.Column(
        db.String(50),
        nullable=True,
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

    supplier_order_confirmation = db.relationship(
        "SupplierOrderConfirmation",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<SupplierOrderConfirmationItem {self.id}>"