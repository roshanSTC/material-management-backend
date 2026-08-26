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

    company_business_name = db.Column(
        db.String(255),
        nullable=False,
    )

    email = db.Column(
        db.String(255),
        nullable=False,
    )

    address = db.Column(
        db.Text,
        nullable=False,
    )

    website = db.Column(
        db.String(2048),
        nullable=True,
    )

    contact_number = db.Column(
        db.String(30),
        nullable=False,
    )

    tender_title = db.Column(
        db.String(255),
        nullable=False,
    )

    tender_number = db.Column(
        db.String(100),
        nullable=False,
    )

    tender_date = db.Column(
        db.Date,
        nullable=False,
    )

    tender_opening_date = db.Column(
        db.Date,
        nullable=False,
    )

    opening_time = db.Column(
        db.Time,
        nullable=False,
    )

    closing_date = db.Column(
        db.Date,
        nullable=False,
    )

    closing_time = db.Column(
        db.Time,
        nullable=False,
    )

    gst_rate = db.Column(
        db.Numeric(5, 2),
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

    incoterms = db.Column(
        db.String(50),
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