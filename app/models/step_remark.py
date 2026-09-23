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

    author = db.relationship(
        "User",
        lazy="joined",
    )

    __table_args__ = (
        db.CheckConstraint(
            "step_number BETWEEN 1 AND 15",
            name="ck_step_remarks_step_number",
        ),
    )

    def __repr__(self) -> str:
        return f"<StepRemark {self.id}: Project {self.project_id} Step {self.step_number}>"

