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

    packing_list_no = db.Column(
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

    net_weight = db.Column(
        db.String(255),
        nullable=True,
    )

    gross_weight = db.Column(
        db.String(255),
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

    # Property aliases for backward/forward compatibility
    @property
    def packing_list_number(self):
        return self.packing_list_no

    @packing_list_number.setter
    def packing_list_number(self, val):
        self.packing_list_no = val

    @property
    def net_weight_kg(self):
        return self.net_weight

    @net_weight_kg.setter
    def net_weight_kg(self, val):
        self.net_weight = val

    @property
    def gross_weight_kg(self):
        return self.gross_weight

    @gross_weight_kg.setter
    def gross_weight_kg(self, val):
        self.gross_weight = val

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, val):
        self.remark = val

    def __repr__(self) -> str:
        return (
            f"<CustomerDeliveryPackingList "
            f"{self.id}: {self.packing_list_no}>"
        )