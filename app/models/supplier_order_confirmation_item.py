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

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    supplier_order_confirmation = db.relationship(
        "SupplierOrderConfirmation",
        back_populates="items",
    )

    # Property aliases for backward/forward compatibility
    @property
    def item_description(self):
        return self.description

    @item_description.setter
    def item_description(self, val):
        self.description = val

    @property
    def hsn(self):
        return self.hsn_code

    @hsn.setter
    def hsn(self, val):
        self.hsn_code = val

    @property
    def hsn_sac(self):
        return self.hsn_code

    @hsn_sac.setter
    def hsn_sac(self, val):
        self.hsn_code = val

    def __repr__(self) -> str:
        return f"<SupplierOrderConfirmationItem {self.id}>"