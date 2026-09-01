from datetime import datetime

from app.extensions.database import db


class Material(db.Model):
    __tablename__ = "materials"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    material_code = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    material_name = db.Column(
        db.String(255),
        nullable=False,
        index=True,
    )

    hsn_code = db.Column(
        db.String(20),
        nullable=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
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

    def __repr__(self) -> str:
        return (
            f"<Material {self.id}: "
            f"{self.material_code} - "
            f"{self.material_name}>"
        )