from datetime import datetime

from app.extensions.database import db


class CostSheetItem(db.Model):
    __tablename__ = "cost_sheet_items"

    id = db.Column(db.Integer, primary_key=True)
    cost_sheet_id = db.Column(
        db.Integer,
        db.ForeignKey("cost_sheets.id"),
        nullable=False,
        index=True,
    )
    item_code = db.Column(db.String(100), nullable=False)
    item_description = db.Column(db.String(500), nullable=False)
    price_per_unit_eur = db.Column(db.Numeric(18, 2), nullable=False)
    quantity = db.Column(db.Numeric(18, 3), nullable=False)
    customs_duty_rate = db.Column(db.Numeric(8, 6), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    cost_sheet = db.relationship("CostSheet", back_populates="items")
    price_history = db.relationship(
        "ItemPriceHistory",
        back_populates="cost_sheet_item",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ItemPriceHistory.created_at.desc()",
    )

    __table_args__ = (
        db.CheckConstraint(
            "price_per_unit_eur > 0",
            name="ck_cost_sheet_items_positive_price",
        ),
        db.CheckConstraint(
            "quantity > 0",
            name="ck_cost_sheet_items_positive_quantity",
        ),
        db.CheckConstraint(
            "customs_duty_rate IS NULL OR customs_duty_rate BETWEEN 0 AND 1",
            name="ck_cost_sheet_items_duty_rate",
        ),
    )

    def __repr__(self) -> str:
        return f"<CostSheetItem {self.id}: {self.item_code}>"
