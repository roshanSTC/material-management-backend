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

    delivery_challan_no = db.Column(
        db.String(100),
        nullable=False,
    )

    delivery_challan_date = db.Column(
        db.Date,
        nullable=False,
    )

    gst_rate = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    gst_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    round_off = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    net_total = db.Column(
        db.Numeric(18, 2),
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
        back_populates="delivery_challans",
        lazy="select",
    )

    items = db.relationship(
        "DeliveryChallanItem",
        back_populates="delivery_challan",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Property aliases for backward/forward compatibility
    @property
    def delivery_challan_number(self):
        return self.delivery_challan_no

    @delivery_challan_number.setter
    def delivery_challan_number(self, val):
        self.delivery_challan_no = val

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, val):
        self.remark = val

    def __repr__(self) -> str:
        return (
            f"<DeliveryChallan "
            f"{self.id}: {self.delivery_challan_no}>"
        )