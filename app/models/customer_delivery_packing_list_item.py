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

    package_no = db.Column(
        db.String(100),
        nullable=True,
    )

    material_name = db.Column(
        db.String(255),
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

    weight = db.Column(
        db.Numeric(18, 3),
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

    packing_list = db.relationship(
        "CustomerDeliveryPackingList",
        back_populates="items",
        lazy="select",
    )

    # Property aliases for backward/forward compatibility
    @property
    def material_description(self):
        return self.material_name

    @material_description.setter
    def material_description(self, val):
        self.material_name = val

    @property
    def hsn_sac(self):
        return self.hsn_code

    @hsn_sac.setter
    def hsn_sac(self, val):
        self.hsn_code = val

    @property
    def weight_per_unit_kg(self):
        return self.weight

    @weight_per_unit_kg.setter
    def weight_per_unit_kg(self, val):
        self.weight = val

    @property
    def total_weight_kg(self):
        return self.weight

    @total_weight_kg.setter
    def total_weight_kg(self, val):
        self.weight = val

    def __repr__(self) -> str:
        return (
            f"<CustomerDeliveryPackingListItem "
            f"{self.id}: {self.material_name}>"
        )