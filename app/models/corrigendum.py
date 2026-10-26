from datetime import datetime

from app.extensions.database import db


class Corrigendum(db.Model):
    __tablename__ = "corrigendums"

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
    corrigendum_no = db.Column(
        db.String(100),
        nullable=False,
    )
    against_tender_no = db.Column(
        db.String(100),
        nullable=True,
    )
    tender_title = db.Column(
        db.String(255),
        nullable=True,
    )
    issue_date = db.Column(
        db.Date,
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
        back_populates="corrigendums",
    )

    def __repr__(self) -> str:
        return f"<Corrigendum {self.id}: {self.corrigendum_no}>"

