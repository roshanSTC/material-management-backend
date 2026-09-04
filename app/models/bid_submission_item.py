from datetime import datetime

from app.extensions.database import db


class BidSubmissionItem(db.Model):
    __tablename__ = "bid_submission_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    bid_submission_id = db.Column(
        db.Integer,
        db.ForeignKey("bid_submissions.id"),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.String(500),
        nullable=False,
    )

    hsn_sac = db.Column(
        db.String(50),
        nullable=True,
    )

    unit_price = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    quantity = db.Column(
        db.Numeric(18, 3),
        nullable=False,
    )

    net_total = db.Column(
        db.Numeric(18, 2),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    bid_submission = db.relationship(
        "BidSubmission",
        back_populates="items",
    )

    @property
    def material_name(self) -> str | None:
        return self.description

    @material_name.setter
    def material_name(self, val: str | None) -> None:
        self.description = val

    @property
    def net_amount(self):
        return self.net_total

    @net_amount.setter
    def net_amount(self, val):
        self.net_total = val

    def __repr__(self) -> str:
        return f"<BidSubmissionItem {self.id}>"