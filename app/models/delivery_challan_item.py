from datetime import datetime

from app.extensions.database import db


class DeliveryChallanItem(db.Model):
    __tablename__ = "delivery_challan_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    delivery_challan_id = db.Column(
        db.Integer,
        db.ForeignKey("delivery_challans.id"),
        nullable=False,
        index=True,
    )

    material_description = db.Column(
        db.String(500),
        nullable=False,
    )

    quantity = db.Column(
        db.Numeric(18, 3),
        nullable=False,
    )

    rate_per_unit = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    amount = db.Column(
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

    delivery_challan = db.relationship(
        "DeliveryChallan",
        back_populates="items",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<DeliveryChallanItem "
            f"{self.id}: {self.material_description}>"
        )