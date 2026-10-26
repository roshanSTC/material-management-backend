from datetime import datetime

from app.extensions.database import db


class LimitedTenderEnquiryItem(db.Model):
    __tablename__ = "limited_tender_enquiry_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    limited_tender_enquiry_id = db.Column(
        db.Integer,
        db.ForeignKey("limited_tender_enquiries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sr_no = db.Column(
        db.Integer,
        nullable=True,
    )
    description = db.Column(
        db.Text,
        nullable=False,
    )
    unit = db.Column(
        db.String(50),
        nullable=True,
    )
    quantity = db.Column(
        db.Numeric(15, 3),
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

    limited_tender_enquiry = db.relationship(
        "LimitedTenderEnquiry",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<LimitedTenderEnquiryItem {self.id}: {self.description[:30]}>"

