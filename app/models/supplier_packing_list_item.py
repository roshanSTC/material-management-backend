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
        default=0.00,
    )

    net_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    weight = db.Column(
        db.Numeric(18, 3),
        nullable=True,
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

    # Property aliases for backward/forward compatibility
    @property
    def supplier_packing_list_id(self):
        return self.packing_list_id

    @supplier_packing_list_id.setter
    def supplier_packing_list_id(self, val):
        self.packing_list_id = val

    @property
    def material_description(self):
        return self.description

    @material_description.setter
    def material_description(self, val):
        self.description = val

    @property
    def unit_weight_kg(self):
        return self.unit_weight

    @unit_weight_kg.setter
    def unit_weight_kg(self, val):
        self.unit_weight = val

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
        return f"<SupplierPackingListItem {self.id}>"