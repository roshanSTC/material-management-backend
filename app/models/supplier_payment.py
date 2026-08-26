from datetime import datetime

from app.extensions.database import db


class SupplierPayment(db.Model):
    __tablename__ = "supplier_payments"

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

    payment_date = db.Column(
        db.Date,
        nullable=False,
    )

    currency = db.Column(
        db.String(10),
        nullable=False,
    )

    amount_paid_currency = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    amount_paid_inr = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    transaction_details = db.Column(
        db.Text,
        nullable=True,
    )

    pending_amount = db.Column(
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
        back_populates="supplier_payments",
    )

    supplier = db.relationship(
        "Supplier",
        back_populates="supplier_payments",
    )

    def __repr__(self) -> str:
        return f"<SupplierPayment {self.id}>"