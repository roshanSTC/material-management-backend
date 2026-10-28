from datetime import datetime

from sqlalchemy import JSON, and_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import foreign

from app.extensions.database import db


class ProjectStep(db.Model):
    __tablename__ = "project_steps"

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

    step_number = db.Column(
        db.Integer,
        nullable=True,
    )

    step_order = db.Column(
        db.Integer,
        nullable=True,
    )

    form_code = db.Column(
        db.String(60),
        db.ForeignKey("form_definitions.form_code"),
        nullable=True,
        index=True,
    )

    step_name = db.Column(
        db.String(255),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="in_progress",
    )

    progress_percentage = db.Column(
        db.Integer,
        nullable=True,
        default=0,
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True,
    )

    data = db.Column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=True,
        default=dict,
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

    form_definition = db.relationship(
        "FormDefinition",
        foreign_keys=[form_code],
    )

    remarks = db.relationship(
        "StepRemark",
        back_populates="step",
        cascade="all, delete-orphan",
        order_by="StepRemark.created_at.desc()",
    )

    step_attachments = db.relationship(
        "Attachment",
        primaryjoin="and_(foreign(Attachment.entity_id) == ProjectStep.id, Attachment.entity_type == 'project_step')",
        cascade="all, delete-orphan",
        order_by="Attachment.created_at.asc()",
    )

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'skipped')",
            name="ck_project_step_status",
        ),
        db.Index(
            "uq_project_steps_project_form_code",
            "project_id",
            "form_code",
            unique=True,
            postgresql_where=db.text("form_code IS NOT NULL"),
            sqlite_where=db.text("form_code IS NOT NULL"),
        ),
    )

    def to_dict(self) -> dict:
        order_val = self.step_order or self.step_number or 1
        fdef = self.form_definition
        if self.data is None:
            clean_data = None
        else:
            clean_data = dict(self.data) if isinstance(self.data, dict) else self.data
            if isinstance(clean_data, dict):
                clean_data.pop("_auto_created", None)
                clean_data.pop("_is_attached", None)
                clean_data.pop("_synced_from_record", None)
                clean_data.pop("_manually_completed", None)
        return {
            "id": self.id,
            "project_id": self.project_id,
            "step_order": order_val,
            "step_number": order_val,
            "form_code": self.form_code or "",
            "step_name": self.step_name or (fdef.name if fdef else ""),
            "description": self.description or (fdef.description if fdef else ""),
            "phase_id": fdef.phase_id if fdef else "",
            "category": fdef.category if fdef else "",
            "icon": fdef.icon if fdef else "pi pi-file",
            "status": self.status or "in_progress",
            "progress_percentage": self.progress_percentage if self.progress_percentage is not None else 0,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "data": clean_data,
            "remarks": [r.to_dict() for r in (self.remarks or [])],
            "attachments": [a.to_dict() for a in (self.step_attachments or [])],
        }

    def __repr__(self) -> str:
        return f"<ProjectStep {self.project_id}: order={self.step_order or self.step_number} form={self.form_code}>"
