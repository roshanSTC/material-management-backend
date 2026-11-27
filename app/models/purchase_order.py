from datetime import datetime

from app.extensions.database import db


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

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

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=True,
        index=True,
    )

    tender_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_tenders.id"),
        nullable=True,
        index=True,
    )

    customer_name = db.Column(
        db.String(255),
        nullable=True,
    )

    po_title = db.Column(
        db.String(255),
        nullable=False,
    )

    po_no = db.Column(
        db.String(100),
        nullable=False,
    )

    poc_name = db.Column(
        db.String(255),
        nullable=True,
    )

    email = db.Column(
        db.String(255),
        nullable=True,
    )

    contact = db.Column(
        db.String(30),
        nullable=True,
    )

    po_date = db.Column(
        db.Date,
        nullable=False,
    )

    gst_rate_pct = db.Column(
        db.Numeric(5, 2),
        nullable=True,
    )

    gst_amount = db.Column(
        db.Numeric(18, 2),
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

    currency_unit = db.Column(
        db.String(20),
        nullable=True,
    )

    currency_symbol = db.Column(
        db.String(20),
        nullable=True,
    )

    delivery_date = db.Column(
        db.Date,
        nullable=True,
    )

    delivery_terms = db.Column(
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
        back_populates="purchase_orders",
    )

    customer = db.relationship(
        "Customer",
        back_populates="purchase_orders",
    )

    tender = db.relationship(
        "CustomerTender",
        back_populates="purchase_orders",
    )

    items = db.relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    supplier_order_confirmations = db.relationship(
        "SupplierOrderConfirmation",
        back_populates="purchase_order",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.id}>"