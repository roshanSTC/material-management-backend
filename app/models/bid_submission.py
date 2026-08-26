from datetime import datetime

from app.extensions.database import db


class BidSubmission(db.Model):
    __tablename__ = "bid_submissions"

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

    tender_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_tenders.id"),
        nullable=False,
        index=True,
    )

    tender_name = db.Column(
        db.String(255),
        nullable=False,
    )

    submission_date = db.Column(
        db.Date,
        nullable=False,
    )

    submission_number = db.Column(
        db.String(100),
        nullable=False,
    )

    delivery_term = db.Column(
        db.String(100),
        nullable=True,
    )

    period = db.Column(
        db.String(100),
        nullable=True,
    )

    payment_term = db.Column(
        db.String(255),
        nullable=True,
    )

    validity = db.Column(
        db.String(100),
        nullable=True,
    )

    warranty_period = db.Column(
        db.String(100),
        nullable=True,
    )

    gst_rate = db.Column(
        db.Numeric(5, 2),
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
        back_populates="bid_submissions",
    )

    tender = db.relationship(
        "CustomerTender",
        back_populates="bid_submissions",
    )

    items = db.relationship(
        "BidSubmissionItem",
        back_populates="bid_submission",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<BidSubmission {self.id}>"