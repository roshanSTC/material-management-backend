from datetime import datetime

from app.extensions.database import db


class ExpressionOfInterest(db.Model):
    __tablename__ = "expressions_of_interest"

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
    eoi_title = db.Column(
        db.String(255),
        nullable=True,
    )
    eoi_no = db.Column(
        db.String(100),
        nullable=False,
    )
    eoi_date = db.Column(
        db.Date,
        nullable=True,
    )
    eoi_closing_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    eoi_opening_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    mode_of_submission = db.Column(
        db.String(100),
        nullable=True,
    )
    supply_location = db.Column(
        db.String(255),
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
        back_populates="expressions_of_interest",
    )
    items = db.relationship(
        "ExpressionOfInterestItem",
        back_populates="expression_of_interest",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ExpressionOfInterestItem.sr_no.asc()",
    )

    def __repr__(self) -> str:
        return f"<ExpressionOfInterest {self.id}: {self.eoi_no}>"

