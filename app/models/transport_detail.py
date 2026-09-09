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

    transport_mode = db.Column(
        db.String(50),
        nullable=False,
    )

    lr_no = db.Column(
        db.String(100),
        nullable=True,
    )

    rr_no = db.Column(
        db.String(100),
        nullable=True,
    )

    awb_no = db.Column(
        db.String(100),
        nullable=True,
    )

    date = db.Column(
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

    @property
    def transportation_mode(self):
        return self.transport_mode

    @transportation_mode.setter
    def transportation_mode(self, value):
        self.transport_mode = value

    @property
    def lr_number(self):
        return self.lr_no

    @lr_number.setter
    def lr_number(self, value):
        self.lr_no = value

    @property
    def transport_date(self):
        return self.date

    @transport_date.setter
    def transport_date(self, value):
        self.date = value

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, value):
        self.remark = value

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
            f"{self.id}: {self.transport_mode}>"
        )