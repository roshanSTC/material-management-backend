from datetime import datetime

from app.extensions.database import db


class LimitedTenderEnquiry(db.Model):
    __tablename__ = "limited_tender_enquiries"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pqb_no = db.Column(
        db.String(100),
        nullable=True,
    )
    tender_title = db.Column(
        db.String(255),
        nullable=True,
    )
    tender_enquiry_no = db.Column(
        db.String(100),
        nullable=False,
    )
    tender_issue_date = db.Column(
        db.Date,
        nullable=True,
    )
    bid_submission_due_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    bid_opening_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    tender_fee = db.Column(
        db.Numeric(15, 2),
        nullable=True,
    )
    emd = db.Column(
        db.Numeric(15, 2),
        nullable=True,
    )
    tender_validity = db.Column(
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
        back_populates="limited_tender_enquiries",
    )
    items = db.relationship(
        "LimitedTenderEnquiryItem",
        back_populates="limited_tender_enquiry",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="LimitedTenderEnquiryItem.sr_no.asc()",
    )

    def __repr__(self) -> str:
        return f"<LimitedTenderEnquiry {self.id}: {self.tender_enquiry_no}>"

