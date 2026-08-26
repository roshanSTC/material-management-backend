from datetime import datetime

from app.extensions.database import db


class WarrantyCertificate(db.Model):
    __tablename__ = "warranty_certificates"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    certificate_date = db.Column(
        db.Date,
        nullable=False,
    )

    warranty_period = db.Column(
        db.String(100),
        nullable=False,
    )

    po_number = db.Column(
        db.String(100),
        nullable=True,
    )

    po_date = db.Column(
        db.Date,
        nullable=True,
    )

    invoice_number = db.Column(
        db.String(100),
        nullable=True,
    )

    invoice_date = db.Column(
        db.Date,
        nullable=True,
    )

    remark = db.Column(
        db.Text,
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

    project = db.relationship(
        "Project",
        back_populates="warranty_certificates",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<WarrantyCertificate "
            f"{self.id}: {self.certificate_date}>"
        )