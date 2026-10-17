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

    upload_key = db.Column(
        db.String(80),
        nullable=True,
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

    def to_dict(self) -> dict:
        size_display = ""
        if self.file_size is not None:
            if self.file_size >= 1024 * 1024:
                size_display = f"{self.file_size / (1024 * 1024):.1f} MB"
            elif self.file_size >= 1024:
                size_display = f"{self.file_size / 1024:.1f} KB"
            else:
                size_display = f"{self.file_size} B"

        return {
            "id": self.id,
            "upload_key": self.upload_key,
            "file_name": self.file_name,
            "file_size": size_display,
            "file_size_bytes": self.file_size,
            "file_path": self.storage_key,
            "mime_type": self.content_type,
            "download_url": f"/api/v1/attachments/{self.id}/download" if self.id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<Attachment {self.id}: "
            f"{self.entity_type}={self.entity_id} "
            f"{self.file_name}>"
        )