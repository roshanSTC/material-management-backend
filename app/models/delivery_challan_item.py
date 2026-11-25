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
        nullable=False,
    )

    total_amount = db.Column(
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
            f"{self.id}: {self.description}>"
        )