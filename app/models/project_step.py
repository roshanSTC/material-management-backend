
from datetime import datetime

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.extensions.database import db


class ProjectStep(db.Model):
    __tablename__ = "project_steps"

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
    )

    step_name = db.Column(
        db.String(255),
        nullable=False,
    )
    
    description = db.Column(
        db.Text,
        nullable=False,
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending",
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    data = db.Column(
        JSONB().with_variant(JSON, "sqlite"),
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
        back_populates="steps",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "step_number",
            name="uq_project_step_number",
        ),
        db.CheckConstraint(
            "step_number BETWEEN 1 AND 15",
            name="ck_project_step_number",
        ),
        db.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed')",
            name="ck_project_step_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<ProjectStep {self.project_id}:{self.step_number}>"

