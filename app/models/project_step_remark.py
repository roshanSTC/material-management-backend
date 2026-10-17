from datetime import datetime

from app.extensions.database import db


class ProjectStepRemark(db.Model):
    __tablename__ = "project_step_remarks"

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
    step_number = db.Column(
        db.Integer,
        nullable=True,
    )
    user_id = db.Column(
        db.Integer,
        nullable=True,
    )
    user_name = db.Column(
        db.String(100),
        nullable=True,
    )
    remark = db.Column(
        db.Text,
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    project = db.relationship(
        "Project",
        backref=db.backref("step_remarks_dynamic", cascade="all, delete-orphan"),
    )
    step = db.relationship(
        "ProjectStep",
        back_populates="remarks",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "remark": self.remark,
            "user": self.user_name or "User",
            "user_name": self.user_name or "User",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<ProjectStepRemark {self.id}: step={self.step_id}>"

