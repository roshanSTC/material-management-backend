from datetime import datetime

from app.extensions.database import db


class SupplierQuotation(db.Model):
    __tablename__ = "supplier_quotations"

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

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    quotation_number = db.Column(
        db.String(100),
        nullable=False,
    )

    quotation_date = db.Column(
        db.Date,
        nullable=False,
    )

    quotation_value = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    currency_unit = db.Column(
        db.String(20),
        nullable=True,
    )

    validity = db.Column(
        db.String(100),
        nullable=True,
    )

    incoterms = db.Column(
        db.String(50),
        nullable=True,
    )

    payment_terms = db.Column(
        db.String(255),
        nullable=True,
    )

    delivery_period = db.Column(
        db.String(100),
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
        back_populates="supplier_quotations",
    )

    supplier = db.relationship(
        "Supplier",
        back_populates="supplier_quotations",
    )

    items = db.relationship(
        "SupplierQuotationItem",
        back_populates="supplier_quotation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<SupplierQuotation {self.id}>"