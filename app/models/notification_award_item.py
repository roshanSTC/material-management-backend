from datetime import datetime

from app.extensions.database import db


class NotificationAwardItem(db.Model):
    __tablename__ = "notification_award_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    notification_award_id = db.Column(
        db.Integer,
        db.ForeignKey("notification_awards.id", ondelete="CASCADE"),
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
    quantity = db.Column(
        db.Numeric(15, 3),
        nullable=True,
    )
    per_unit_price = db.Column(
        db.Numeric(15, 2),
        nullable=True,
    )
    total_amount = db.Column(
        db.Numeric(15, 2),
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

    notification_award = db.relationship(
        "NotificationAward",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<NotificationAwardItem {self.id}: {self.description[:30]}>"

