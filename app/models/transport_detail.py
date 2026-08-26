from datetime import datetime

from app.extensions.database import db


class TransportDetail(db.Model):
    __tablename__ = "transport_details"

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

    transportation_mode = db.Column(
        db.String(100),
        nullable=False,
    )

    lr_number = db.Column(
        db.String(100),
        nullable=True,
    )

    transport_date = db.Column(
        db.Date,
        nullable=False,
    )

    from_location = db.Column(
        db.String(255),
        nullable=False,
    )

    to_location = db.Column(
        db.String(255),
        nullable=False,
    )

    transport_charges = db.Column(
        db.Numeric(18, 2),
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
        back_populates="transport_details",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<TransportDetail "
            f"{self.id}: {self.transportation_mode}>"
        )