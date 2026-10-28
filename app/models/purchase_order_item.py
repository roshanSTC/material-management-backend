from datetime import datetime

from app.extensions.database import db


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    purchase_order_id = db.Column(
        db.Integer,
        db.ForeignKey("purchase_orders.id"),
        nullable=False,
        index=True,
    )

    material_name = db.Column(
        db.String(255),
        nullable=True,
    )

    description = db.Column(
        db.String(500),
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
        nullable=True,
    )

    unit = db.Column(
        db.String(50),
        nullable=True,
        default="NOS",
    )

    delivery_date = db.Column(
        db.Date,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    purchase_order = db.relationship(
        "PurchaseOrder",
        back_populates="items",
    )

    @property
    def hsn_sac(self):
        return self.hsn_code

    @hsn_sac.setter
    def hsn_sac(self, val):
        self.hsn_code = val

    @property
    def total_price(self):
        return self.net_amount

    @total_price.setter
    def total_price(self, val):
        self.net_amount = val

    def __repr__(self) -> str:
        return f"<PurchaseOrderItem {self.id}>"