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
        nullable=True,
        index=True,
    )

    currency = db.Column(
        db.String(10),
        nullable=False,
        default="INR",
    )

    payment_percentage = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    total_supplier_value = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    amount_paid = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    payment_date = db.Column(
        db.Date,
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

    @property
    def amount_paid_inr(self):
        return self.amount_paid

    @amount_paid_inr.setter
    def amount_paid_inr(self, value):
        self.amount_paid = value

    @property
    def amount_paid_currency(self):
        return self.amount_paid

    @amount_paid_currency.setter
    def amount_paid_currency(self, value):
        self.amount_paid = value

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, value):
        self.remark = value

    def __repr__(self) -> str:
        return f"<SupplierPayment {self.id}>"