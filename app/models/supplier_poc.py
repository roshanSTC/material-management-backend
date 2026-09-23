from datetime import datetime

from app.extensions.database import db


class SupplierPoc(db.Model):
    __tablename__ = "supplier_pocs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
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

    supplier = db.relationship(
        "Supplier",
        back_populates="pocs",
    )

    def __repr__(self) -> str:
        return f"<SupplierPoc {self.id}: {self.name}>"

