from datetime import datetime

from app.extensions.database import db


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    entity_type = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    entity_id = db.Column(
        db.Integer,
        nullable=False,
        index=True,
    )

    file_name = db.Column(
        db.String(255),
        nullable=False,
    )

    storage_key = db.Column(
        db.String(1024),
        nullable=False,
        unique=True,
    )

    content_type = db.Column(
        db.String(100),
        nullable=False,
    )

    file_size = db.Column(
        db.BigInteger,
        nullable=False,
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
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

    uploader = db.relationship(
        "User",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Attachment {self.id}: "
            f"{self.entity_type}={self.entity_id} "
            f"{self.file_name}>"
        )