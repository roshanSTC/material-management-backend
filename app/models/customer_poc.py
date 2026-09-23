from datetime import datetime

from app.extensions.database import db


class CustomerPoc(db.Model):
    __tablename__ = "customer_pocs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(255),
        nullable=False,
    )

    email = db.Column(
        db.String(255),
        nullable=True,
    )

    contact_number = db.Column(
        db.String(30),
        nullable=True,
    )

    designation = db.Column(
        db.String(255),
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

    customer = db.relationship(
        "Customer",
        back_populates="pocs",
    )

    def __repr__(self) -> str:
        return f"<CustomerPoc {self.id}: {self.name}>"

