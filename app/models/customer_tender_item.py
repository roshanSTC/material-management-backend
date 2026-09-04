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

    item_code = db.Column(
        db.String(100),
        nullable=True,
    )

    description = db.Column(
        db.String(500),
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

    customer_tender = db.relationship(
        "CustomerTender",
        back_populates="items",
    )

    @property
    def material_name(self) -> str | None:
        return self.description

    @material_name.setter
    def material_name(self, val: str | None) -> None:
        self.description = val

    def __repr__(self) -> str:
        return f"<CustomerTenderItem {self.id}>"