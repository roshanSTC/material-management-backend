from datetime import datetime

from app.extensions.database import db


class CustomerPayment(db.Model):
    __tablename__ = "customer_payments"

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

    invoice_no = db.Column(
        db.String(100),
        nullable=False,
    )

    invoice_date = db.Column(
        db.Date,
        nullable=False,
    )

    invoice_value = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    payment_amount = db.Column(
        db.Numeric(18, 2),
        nullable=False,
    )

    payment_date = db.Column(
        db.Date,
        nullable=False,
    )

    ld = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    tds = db.Column(
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
        back_populates="customer_payments",
    )

    @property
    def invoice_number(self) -> str:
        return self.invoice_no

    @invoice_number.setter
    def invoice_number(self, value: str):
        self.invoice_no = value

    @property
    def liquidated_damages(self):
        return self.ld

    @liquidated_damages.setter
    def liquidated_damages(self, value):
        self.ld = value

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, value):
        self.remark = value

    def __repr__(self) -> str:
        return f"<CustomerPayment {self.id}>"