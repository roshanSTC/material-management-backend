from datetime import datetime

from app.extensions.database import db


class QuotationRequestItem(db.Model):
    __tablename__ = "quotation_request_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    quotation_request_id = db.Column(
        db.Integer,
        db.ForeignKey("quotation_requests.id"),
        nullable=False,
        index=True,
    )

    material_name = db.Column(
        db.String(255),
        nullable=False,
    )

    quantity = db.Column(
        db.Numeric(18, 3),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    quotation_request = db.relationship(
        "QuotationRequest",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<QuotationRequestItem {self.id}>"