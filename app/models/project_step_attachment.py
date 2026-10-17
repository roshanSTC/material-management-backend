from datetime import datetime

from app.extensions.database import db


class ProjectStepAttachment(db.Model):
    __tablename__ = "project_step_attachments"

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
    step_id = db.Column(
        db.Integer,
        db.ForeignKey("project_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    upload_key = db.Column(
        db.String(80),
        nullable=False,
    )
    file_name = db.Column(
        db.String(255),
        nullable=False,
    )
    file_path = db.Column(
        db.String(500),
        nullable=False,
    )
    file_size_bytes = db.Column(
        db.BigInteger,
        nullable=True,
    )
    mime_type = db.Column(
        db.String(100),
        nullable=True,
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    project = db.relationship(
        "Project",
        backref=db.backref("step_attachments_dynamic", cascade="all, delete-orphan"),
    )
    step = db.relationship(
        "ProjectStep",
        back_populates="step_attachments",
    )

    def to_dict(self) -> dict:
        size_display = ""
        if self.file_size_bytes is not None:
            if self.file_size_bytes >= 1024 * 1024:
                size_display = f"{self.file_size_bytes / (1024 * 1024):.1f} MB"
            elif self.file_size_bytes >= 1024:
                size_display = f"{self.file_size_bytes / 1024:.1f} KB"
            else:
                size_display = f"{self.file_size_bytes} B"

        return {
            "id": self.id,
            "upload_key": self.upload_key,
            "file_name": self.file_name,
            "file_size": size_display,
            "file_size_bytes": self.file_size_bytes,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "download_url": f"/api/v1/attachments/{self.id}/download" if self.id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<ProjectStepAttachment {self.id}: step={self.step_id} key={self.upload_key}>"

