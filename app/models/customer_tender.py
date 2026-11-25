from datetime import datetime

from app.extensions.database import db


class CustomerTender(db.Model):
    __tablename__ = "customer_tenders"

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

    customer_name = db.Column(
        db.String(255),
        nullable=True,
    )

    officer_name = db.Column(
        db.String(255),
        nullable=True,
    )

    email = db.Column(
        db.String(255),
        nullable=True,
    )

    address = db.Column(
        db.Text,
        nullable=True,
    )

    website = db.Column(
        db.String(2048),
        nullable=True,
    )

    contact_number = db.Column(
        db.String(30),
        nullable=True,
    )

    tender_title = db.Column(
        db.String(255),
        nullable=True,
    )

    tender_no = db.Column(
        db.String(100),
        nullable=False,
    )

    tender_issue_date = db.Column(
        db.DateTime,
        nullable=True,
    )

    opening_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )

    closing_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )

    tender_fee = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    validity = db.Column(
        db.String(100),
        nullable=True,
    )

    delivery_terms = db.Column(
        db.String(255),
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
        back_populates="customer_tenders",
    )

    customer = db.relationship(
        "Customer",
        lazy="select",
    )

    items = db.relationship(
        "CustomerTenderItem",
        back_populates="customer_tender",
        cascade="all, delete-orphan",
        lazy="select",
    )

    bid_submissions = db.relationship(
        "BidSubmission",
        back_populates="tender",
        lazy="select",
    )

    purchase_orders = db.relationship(
        "PurchaseOrder",
        back_populates="tender",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<CustomerTender {self.id}>"