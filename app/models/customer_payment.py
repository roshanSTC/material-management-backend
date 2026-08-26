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

    invoice_number = db.Column(
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

    liquidated_damages = db.Column(
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

    def __repr__(self) -> str:
        return f"<CustomerPayment {self.id}>"