from datetime import datetime

from app.extensions.database import db


class CustomerQueryItem(db.Model):
    __tablename__ = "customer_query_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    customer_query_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_queries.id"),
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

    customer_query = db.relationship(
        "CustomerQuery",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<CustomerQueryItem {self.id}>"