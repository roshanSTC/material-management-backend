from datetime import datetime

from app.extensions.database import db


class DeliveryChallan(db.Model):
    __tablename__ = "delivery_challans"

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

    delivery_challan_number = db.Column(
        db.String(100),
        nullable=False,
    )

    delivery_challan_date = db.Column(
        db.Date,
        nullable=False,
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
        back_populates="delivery_challans",
        lazy="select",
    )

    items = db.relationship(
        "DeliveryChallanItem",
        back_populates="delivery_challan",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<DeliveryChallan "
            f"{self.id}: {self.delivery_challan_number}>"
        )