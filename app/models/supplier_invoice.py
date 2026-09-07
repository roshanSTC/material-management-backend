from datetime import datetime

from app.extensions.database import db


class SupplierInvoice(db.Model):
    __tablename__ = "supplier_invoices"

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
        nullable=False,
        index=True,
    )

    invoice_no = db.Column(
        db.String(100),
        nullable=False,
    )

    invoice_date = db.Column(
        db.Date,
        nullable=False,
    )

    delivery_terms = db.Column(
        db.String(100),
        nullable=True,
    )

    delivery_period = db.Column(
        db.String(100),
        nullable=True,
    )

    payment_terms = db.Column(
        db.String(255),
        nullable=True,
    )

    warranty_period = db.Column(
        db.String(100),
        nullable=True,
    )

    total_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    total_net_amount = db.Column(
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
        lazy="select",
    )

    supplier = db.relationship(
        "Supplier",
        lazy="select",
    )

    items = db.relationship(
        "SupplierInvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Property aliases for backward/forward compatibility
    @property
    def invoice_number(self):
        return self.invoice_no

    @invoice_number.setter
    def invoice_number(self, val):
        self.invoice_no = val

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, val):
        self.remark = val

    @property
    def delivery_term(self):
        return self.delivery_terms

    @delivery_term.setter
    def delivery_term(self, val):
        self.delivery_terms = val

    @property
    def payment_term(self):
        return self.payment_terms

    @payment_term.setter
    def payment_term(self, val):
        self.payment_terms = val

    def __repr__(self) -> str:
        return f"<SupplierInvoice {self.id}>"