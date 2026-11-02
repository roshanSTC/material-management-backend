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
        nullable=True,
        index=True,
    )

    supplier_name = db.Column(
        db.String(255),
        nullable=True,
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

    currency_symbol = db.Column(
        db.String(20),
        nullable=True,
    )

    currency = db.Column(
        db.String(20),
        nullable=True,
    )

    total_net_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    total_gross_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    total_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="completed",
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

    warranty_period = db.Column(
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

    @property
    def quotation_no(self):
        return self.quotation_number

    @quotation_no.setter
    def quotation_no(self, val):
        self.quotation_number = val

    @property
    def quotation_validity(self):
        return self.validity

    @quotation_validity.setter
    def quotation_validity(self, val):
        self.validity = val

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, val):
        self.remark = val

    def __repr__(self) -> str:
        return f"<SupplierQuotation {self.id}>"