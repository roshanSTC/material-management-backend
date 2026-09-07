from datetime import datetime

from app.extensions.database import db


class SupplierOrderConfirmation(db.Model):
    __tablename__ = "supplier_order_confirmations"

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

    purchase_order_id = db.Column(
        db.Integer,
        db.ForeignKey("purchase_orders.id"),
        nullable=True,
        index=True,
    )

    order_confirmation_date = db.Column(
        db.Date,
        nullable=False,
    )

    email = db.Column(
        db.String(255),
        nullable=True,
    )

    ref_no = db.Column(
        db.String(100),
        nullable=False,
    )

    shipping_terms = db.Column(
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
        back_populates="supplier_order_confirmations",
    )

    supplier = db.relationship(
        "Supplier",
        back_populates="supplier_order_confirmations",
    )

    purchase_order = db.relationship(
        "PurchaseOrder",
        back_populates="supplier_order_confirmations",
    )

    items = db.relationship(
        "SupplierOrderConfirmationItem",
        back_populates="supplier_order_confirmation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Property aliases for backward/forward compatibility
    @property
    def confirmation_date(self):
        return self.order_confirmation_date

    @confirmation_date.setter
    def confirmation_date(self, val):
        self.order_confirmation_date = val

    @property
    def reference_number(self):
        return self.ref_no

    @reference_number.setter
    def reference_number(self, val):
        self.ref_no = val

    @property
    def shipping_term(self):
        return self.shipping_terms

    @shipping_term.setter
    def shipping_term(self, val):
        self.shipping_terms = val

    @property
    def delivery_term(self):
        return self.delivery_period

    @delivery_term.setter
    def delivery_term(self, val):
        self.delivery_period = val

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, val):
        self.remark = val

    def __repr__(self) -> str:
        return f"<SupplierOrderConfirmation {self.id}>"