from datetime import datetime

from app.extensions.database import db


class NotificationAward(db.Model):
    __tablename__ = "notification_awards"

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
    nac_no = db.Column(
        db.String(100),
        nullable=False,
    )
    nac_date = db.Column(
        db.Date,
        nullable=True,
    )
    nac_title = db.Column(
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
        back_populates="notification_awards",
    )
    items = db.relationship(
        "NotificationAwardItem",
        back_populates="notification_award",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="NotificationAwardItem.sr_no.asc()",
    )

    def __repr__(self) -> str:
        return f"<NotificationAward {self.id}: {self.nac_no}>"

