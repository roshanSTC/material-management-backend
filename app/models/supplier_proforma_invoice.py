from datetime import datetime

from app.extensions.database import db


class SupplierProformaInvoice(db.Model):
    __tablename__ = "supplier_proforma_invoices"

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

    order_confirmation_id = db.Column(
        db.Integer,
        db.ForeignKey("supplier_order_confirmations.id"),
        nullable=True,
        index=True,
    )

    proforma_invoice_no = db.Column(
        db.String(100),
        nullable=False,
    )

    proforma_invoice_date = db.Column(
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

    delivery_date = db.Column(
        db.Date,
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

    order_confirmation = db.relationship(
        "SupplierOrderConfirmation",
        lazy="select",
    )

    items = db.relationship(
        "SupplierProformaInvoiceItem",
        back_populates="proforma_invoice",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Property aliases for backward/forward compatibility
    @property
    def proforma_invoice_number(self):
        return self.proforma_invoice_no

    @proforma_invoice_number.setter
    def proforma_invoice_number(self, val):
        self.proforma_invoice_no = val

    @property
    def invoice_date(self):
        return self.proforma_invoice_date

    @invoice_date.setter
    def invoice_date(self, val):
        self.proforma_invoice_date = val

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

    def __repr__(self) -> str:
        return f"<SupplierProformaInvoice {self.id}>"