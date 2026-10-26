from datetime import datetime

from app.extensions.database import db


class PreQualificationBid(db.Model):
    __tablename__ = "pre_qualification_bids"

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
    pqb_title = db.Column(
        db.String(255),
        nullable=True,
    )
    pqb_no = db.Column(
        db.String(100),
        nullable=False,
    )
    pqb_issuing_date = db.Column(
        db.Date,
        nullable=True,
    )
    pqb_closing_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    pqb_opening_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    mode_of_bid_submission = db.Column(
        db.String(100),
        nullable=True,
    )
    supply_location = db.Column(
        db.String(255),
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
        back_populates="pre_qualification_bids",
    )
    items = db.relationship(
        "PreQualificationBidItem",
        back_populates="pre_qualification_bid",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="PreQualificationBidItem.sr_no.asc()",
    )

    def __repr__(self) -> str:
        return f"<PreQualificationBid {self.id}: {self.pqb_no}>"

