from datetime import datetime

from app.extensions.database import db


class EWayBill(db.Model):
    __tablename__ = "eway_bills"

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

    eway_bill_no = db.Column(
        db.String(100),
        nullable=True,
    )

    eway_bill_date = db.Column(
        db.Date,
        nullable=True,
    )

    valid_from = db.Column(
        db.Date,
        nullable=True,
    )

    valid_until = db.Column(
        db.Date,
        nullable=True,
    )

    document_no = db.Column(
        db.String(100),
        nullable=True,
    )

    document_date = db.Column(
        db.Date,
        nullable=True,
    )

    value = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    place_of_dispatch = db.Column(
        db.String(255),
        nullable=True,
    )

    place_of_delivery = db.Column(
        db.String(255),
        nullable=True,
    )

    transporter = db.Column(
        db.String(255),
        nullable=True,
    )

    mode = db.Column(
        db.String(50),
        nullable=True,
    )

    vehicle_trans_doc_no = db.Column(
        db.String(100),
        nullable=True,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="completed",
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
        back_populates="eway_bills",
        lazy="select",
    )

    items = db.relationship(
        "EWayBillItem",
        back_populates="eway_bill",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def eway_bill_number(self):
        return self.eway_bill_no

    @eway_bill_number.setter
    def eway_bill_number(self, val):
        self.eway_bill_no = val

    @property
    def document_number(self):
        return self.document_no

    @document_number.setter
    def document_number(self, val):
        self.document_no = val

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, val):
        self.remark = val

    def __repr__(self) -> str:
        return f"<EWayBill {self.id}: {self.eway_bill_no}>"


class EWayBillItem(db.Model):
    __tablename__ = "eway_bill_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    eway_bill_id = db.Column(
        db.Integer,
        db.ForeignKey("eway_bills.id"),
        nullable=False,
        index=True,
    )

    sr_no = db.Column(
        db.Integer,
        nullable=True,
    )

    material_name = db.Column(
        db.String(255),
        nullable=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    hsn_sac = db.Column(
        db.String(50),
        nullable=True,
    )

    quantity = db.Column(
        db.Numeric(18, 3),
        nullable=True,
    )

    unit = db.Column(
        db.String(50),
        nullable=True,
    )

    unit_price = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    total_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    eway_bill = db.relationship(
        "EWayBill",
        back_populates="items",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<EWayBillItem {self.id}: {self.material_name}>"

