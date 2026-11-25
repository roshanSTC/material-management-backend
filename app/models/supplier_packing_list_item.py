from datetime import datetime

from app.extensions.database import db


class SupplierPackingListItem(db.Model):
    __tablename__ = "supplier_packing_list_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    packing_list_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_packing_lists.id"),
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
        nullable=True,
    )

    unit_price = db.Column(
        db.Numeric(18, 2),
        nullable=True,
        default=0.00,
    )

    unit_weight = db.Column(
        db.Numeric(18, 3),
        nullable=True,
    )

    total_weight = db.Column(
        db.Numeric(18, 3),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    packing_list = db.relationship(
        "SupplierPackingList",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<SupplierPackingListItem {self.id}>"