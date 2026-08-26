from datetime import datetime

from app.extensions.database import db


class CustomerDeliveryPackingListItem(db.Model):
    __tablename__ = "customer_delivery_packing_list_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    packing_list_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_delivery_packing_lists.id"),
        nullable=False,
        index=True,
    )

    material_description = db.Column(
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

    weight_per_unit_kg = db.Column(
        db.Numeric(18, 3),
        nullable=False,
    )

    total_weight_kg = db.Column(
        db.Numeric(18, 3),
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

    packing_list = db.relationship(
        "CustomerDeliveryPackingList",
        back_populates="items",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerDeliveryPackingListItem "
            f"{self.id}: {self.material_description}>"
        )