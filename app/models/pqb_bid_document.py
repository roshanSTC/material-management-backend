from datetime import datetime

from app.extensions.database import db


class PqbBidDocument(db.Model):
    __tablename__ = "pqb_bid_documents"

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
    pqb_title = db.Column(
        db.String(255),
        nullable=True,
    )
    pqb_no = db.Column(
        db.String(100),
        nullable=False,
    )
    pqb_issue_date = db.Column(
        db.Date,
        nullable=True,
    )
    pqb_closing_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    pqb_opening_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    total_corrigendum_issued = db.Column(
        db.Integer,
        default=0,
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
        back_populates="pqb_bid_documents",
    )

    def __repr__(self) -> str:
        return f"<PqbBidDocument {self.id}: {self.pqb_no}>"

