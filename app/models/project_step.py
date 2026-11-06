from datetime import datetime

from sqlalchemy import JSON, and_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import foreign

from app.extensions.database import db


def is_date_key_name(k: str) -> bool:
    if not isinstance(k, str):
        return False
    k_lower = k.lower().strip()
    EXCLUSIONS = {
        "liquidated_damages", "liquidated", "ld",
        "candidate", "candidates",
        "update", "updated", "updates", "updated_at",
        "validate", "validation", "validations",
        "accommodate", "mandate", "created_at", "completed_at",
    }
    if k_lower in EXCLUSIONS or k_lower.startswith("_"):
        return False
    if any(ex in k_lower for ex in ("liquidated", "candidate", "update", "validation")):
        return False

    if k_lower in ("valid_from", "valid_until", "date"):
        return True
    if k_lower.endswith(("_date", "_time", "_datetime", "_due")):
        return True
    if k_lower.startswith(("date_", "time_")):
        return True
    if "_date_" in k_lower or "_time_" in k_lower or "_datetime_" in k_lower:
        return True
    return False


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

    def _extract_date_fields(self) -> dict:
        dates = {}
        # 1. From self.data
        if isinstance(self.data, dict):
            for k, v in self.data.items():
                if is_date_key_name(k):
                    dates[k] = v.isoformat() if hasattr(v, "isoformat") else v

        # 2. Check underlying entity if attached to project
        if self.project and self.form_code:
            try:
                from app.routes.project_step import FORM_REL_DICT
                rel_attr = FORM_REL_DICT.get(self.form_code)
                if rel_attr:
                    attrs = [rel_attr] if isinstance(rel_attr, str) else rel_attr
                    recs = []
                    for a in attrs:
                        val = getattr(self.project, a, None)
                        if val:
                            if hasattr(val, "__iter__"):
                                recs.extend(list(val))
                            else:
                                recs.append(val)
                    if recs:
                        recs.sort(key=lambda r: getattr(r, "id", 0) or 0, reverse=True)
                        latest_rec = recs[0]
                        if self.form_code == "FORM_33_STE":
                            m = [r for r in recs if getattr(r, "form_code", "") in ("FORM_33_STE", "FORM_33_SINGLE_TENDER_ENQUIRY", "FORM_33", "FORM_STE", "FORM_30_SINGLE_TENDER_ENQUIRY", "FORM_30_STE")]
                            if m:
                                latest_rec = m[0]
                        elif self.form_code == "FORM_30_TECHNO_COMMERCIAL_TENDER":
                            m = [r for r in recs if getattr(r, "form_code", "") in ("FORM_30_TECHNO_COMMERCIAL_TENDER", "FORM_30_TCT", "FORM_30")]
                            if m:
                                latest_rec = m[0]
                        for col in latest_rec.__table__.columns:
                            c_name = col.name
                            if is_date_key_name(c_name):
                                if c_name not in dates or dates[c_name] is None:
                                    val = getattr(latest_rec, c_name, None)
                                    if val is not None:
                                        dates[c_name] = val.isoformat() if hasattr(val, "isoformat") else str(val)
            except Exception:
                pass
        return dates

    def to_dict(self, include_data: bool = False) -> dict:
        from flask import has_request_context, request
        if not include_data and has_request_context():
            if request.args.get("include_data") in ("true", "1"):
                include_data = True

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

        dates = self._extract_date_fields()

        res = {
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
            "remarks": [r.to_dict() for r in (self.remarks or [])],
            "attachments": [a.to_dict() for a in (self.step_attachments or [])],
        }
        if include_data:
            res["data"] = clean_data
        res.update(dates)
        return res

    def __repr__(self) -> str:
        return f"<ProjectStep {self.project_id}: order={self.step_order or self.step_number} form={self.form_code}>"
