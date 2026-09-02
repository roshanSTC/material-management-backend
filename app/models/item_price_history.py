from datetime import datetime

from app.extensions.database import db


class ItemPriceHistory(db.Model):
    __tablename__ = "item_price_history"

    id = db.Column(db.Integer, primary_key=True)
    cost_sheet_item_id = db.Column(
        db.Integer,
        db.ForeignKey("cost_sheet_items.id"),
        nullable=False,
        index=True,
    )
    old_price_eur = db.Column(db.Numeric(18, 2), nullable=False)
    new_price_eur = db.Column(db.Numeric(18, 2), nullable=False)
    supplier_name = db.Column(db.String(255), nullable=False)
    change_reason = db.Column(db.Text, nullable=False)
    changed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    cost_sheet_item = db.relationship("CostSheetItem", back_populates="price_history")
    changed_by_user = db.relationship("User", foreign_keys=[changed_by], lazy="select")

    __table_args__ = (
        db.CheckConstraint(
            "old_price_eur > 0 AND new_price_eur > 0",
            name="ck_item_price_history_positive_prices",
        ),
    )

    def __repr__(self) -> str:
        return f"<ItemPriceHistory {self.id}: item={self.cost_sheet_item_id}>"
