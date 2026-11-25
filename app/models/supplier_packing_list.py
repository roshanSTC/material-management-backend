from datetime import datetime

from app.extensions.database import db


class SupplierPackingList(db.Model):
    __tablename__ = "supplier_packing_lists"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=True,
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

    packing_condition = db.Column(
        db.String(255),
        nullable=True,
    )

    net_weight = db.Column(
        db.Numeric(18, 3),
        nullable=True,
    )

    gross_weight = db.Column(
        db.Numeric(18, 3),
        nullable=True,
    )

    total_no_packages = db.Column(
        db.Integer,
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
        lazy="select",
    )

    supplier = db.relationship(
        "Supplier",
        lazy="select",
    )

    items = db.relationship(
        "SupplierPackingListItem",
        back_populates="packing_list",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<SupplierPackingList {self.id}>"