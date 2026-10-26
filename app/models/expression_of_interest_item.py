from datetime import datetime

from app.extensions.database import db


class ExpressionOfInterestItem(db.Model):
    __tablename__ = "expression_of_interest_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    expression_of_interest_id = db.Column(
        db.Integer,
        db.ForeignKey("expressions_of_interest.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sr_no = db.Column(
        db.Integer,
        nullable=True,
    )
    description = db.Column(
        db.Text,
        nullable=False,
    )
    unit = db.Column(
        db.String(50),
        nullable=True,
    )
    quantity = db.Column(
        db.Numeric(15, 3),
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

    expression_of_interest = db.relationship(
        "ExpressionOfInterest",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<ExpressionOfInterestItem {self.id}: {self.description[:30]}>"

