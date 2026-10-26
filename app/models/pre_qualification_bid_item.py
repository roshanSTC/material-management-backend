from datetime import datetime

from app.extensions.database import db


class PreQualificationBidItem(db.Model):
    __tablename__ = "pre_qualification_bid_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    pre_qualification_bid_id = db.Column(
        db.Integer,
        db.ForeignKey("pre_qualification_bids.id", ondelete="CASCADE"),
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

    pre_qualification_bid = db.relationship(
        "PreQualificationBid",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<PreQualificationBidItem {self.id}: {self.description[:30]}>"

