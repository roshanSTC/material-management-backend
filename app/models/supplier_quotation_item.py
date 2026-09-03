from datetime import datetime

from app.extensions.database import db


class SupplierQuotationItem(db.Model):
    __tablename__ = "supplier_quotation_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    supplier_quotation_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_quotations.id"),
        nullable=False,
        index=True,
    )

    material_name = db.Column(
        db.String(255),
        nullable=False,
    )

    quantity = db.Column(
        db.Numeric(18, 3),
        nullable=False,
    )

    unit_price = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    net_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    supplier_quotation = db.relationship(
        "SupplierQuotation",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<SupplierQuotationItem {self.id}>"