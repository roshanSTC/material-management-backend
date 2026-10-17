from datetime import datetime

from app.extensions.database import db


class StepRemark(db.Model):
    __tablename__ = "step_remarks"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    step_number = db.Column(
        db.Integer,
        nullable=False,
        index=True,
    )

    entity_id = db.Column(
        db.Integer,
        nullable=True,
        index=True,
    )

    remark = db.Column(
        db.Text,
        nullable=False,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    step_id = db.Column(
        db.Integer,
        db.ForeignKey("project_steps.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    user_name = db.Column(
        db.String(100),
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
        back_populates="step_remarks",
    )

    step = db.relationship(
        "ProjectStep",
        back_populates="remarks",
    )

    author = db.relationship(
        "User",
        lazy="joined",
    )

    __table_args__ = (
        db.CheckConstraint(
            "step_number >= 1",
            name="ck_step_remarks_step_number",
        ),
    )

    def to_dict(self) -> dict:
        user_display = self.user_name
        if not user_display and self.author:
            name_parts = [p for p in (self.author.first_name, self.author.last_name) if p]
            user_display = " ".join(name_parts) if name_parts else self.author.email

        return {
            "id": self.id,
            "project_id": self.project_id,
            "step_id": self.step_id,
            "step_number": self.step_number,
            "user_id": self.user_id,
            "user_name": user_display or "User",
            "user": user_display or "User",
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<StepRemark {self.id}: Project {self.project_id} Step {self.step_number}>"

