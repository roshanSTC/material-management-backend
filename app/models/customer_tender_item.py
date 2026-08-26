from datetime import datetime

from app.extensions.database import db


class CustomerTenderItem(db.Model):
    __tablename__ = "customer_tender_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    customer_tender_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_tenders.id"),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.String(500),
        nullable=False,
    )

    hsn_sac = db.Column(
        db.String(50),
        nullable=True,
    )

    unit_price = db.Column(
        db.Numeric(18, 2),
        nullable=True,
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

    customer_tender = db.relationship(
        "CustomerTender",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<CustomerTenderItem {self.id}>"