from datetime import datetime

from app.extensions.database import db


class CustomerDeliveryPackingList(db.Model):
    __tablename__ = "customer_delivery_packing_lists"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    packing_list_number = db.Column(
        db.String(100),
        nullable=False,
    )

    packing_list_date = db.Column(
        db.Date,
        nullable=False,
    )

    total_no_of_packs = db.Column(
        db.Integer,
        nullable=True,
    )

    packing_condition = db.Column(
        db.String(255),
        nullable=True,
    )

    net_weight_kg = db.Column(
        db.Numeric(18, 3),
        nullable=True,
    )

    gross_weight_kg = db.Column(
        db.Numeric(18, 3),
        nullable=True,
    )

    remark = db.Column(
        db.Text,
        nullable=True,
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

    project = db.relationship(
        "Project",
        back_populates="customer_delivery_packing_lists",
        lazy="select",
    )

    items = db.relationship(
        "CustomerDeliveryPackingListItem",
        back_populates="packing_list",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerDeliveryPackingList "
            f"{self.id}: {self.packing_list_number}>"
        )