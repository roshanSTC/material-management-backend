from datetime import datetime

from app.extensions.database import db


class CustomerQuotation(db.Model):
    __tablename__ = "customer_quotations"

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
        nullable=False,
        index=True,
    )

    qo_number = db.Column(
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
        back_populates="customer_quotations",
    )

    customer = db.relationship(
        "Customer",
        back_populates="customer_quotations",
    )

    items = db.relationship(
        "CustomerQuotationItem",
        back_populates="customer_quotation",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<CustomerQuotation {self.id}>"