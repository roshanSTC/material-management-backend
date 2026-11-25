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
        nullable=True,
        index=True,
    )

    customer_name = db.Column(
        db.String(255),
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
        db.Date,
        nullable=True,
    )

    total_no_corrigendum_issued = db.Column(
        db.Integer,
        default=0,
        nullable=True,
    )

    bid_submission_date = db.Column(
        db.DateTime,
        nullable=True,
    )

    delivery_terms = db.Column(
        db.String(100),
        nullable=True,
    )

    delivery_period = db.Column(
        db.String(100),
        nullable=True,
    )

    bid_validity = db.Column(
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

    gst_pct = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    total_net_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    gst_amount = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    total_gross_amount = db.Column(
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