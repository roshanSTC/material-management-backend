from datetime import datetime

from app.extensions.database import db


class BidSubmission(db.Model):
    __tablename__ = "bid_submissions"

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

    tender_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_tenders.id"),
        nullable=True,
        index=True,
    )

    tender_title = db.Column(
        db.String(255),
        nullable=True,
    )

    submission_date = db.Column(
        db.DateTime,
        nullable=True,
    )

    tender_number = db.Column(
        db.String(100),
        nullable=False,
    )

    delivery_term = db.Column(
        db.String(100),
        nullable=True,
    )

    delivery_period = db.Column(
        db.String(100),
        nullable=True,
    )

    payment_term = db.Column(
        db.String(255),
        nullable=True,
    )

    validity = db.Column(
        db.String(100),
        nullable=True,
    )

    warranty_period = db.Column(
        db.String(100),
        nullable=True,
    )

    gst_rate = db.Column(
        db.Numeric(5, 2),
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
        back_populates="bid_submissions",
    )

    tender = db.relationship(
        "CustomerTender",
        back_populates="bid_submissions",
    )

    items = db.relationship(
        "BidSubmissionItem",
        back_populates="bid_submission",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def tender_name(self) -> str | None:
        return self.tender_title

    @tender_name.setter
    def tender_name(self, val: str | None) -> None:
        self.tender_title = val

    @property
    def submission_number(self) -> str:
        return self.tender_number

    @submission_number.setter
    def submission_number(self, val: str) -> None:
        self.tender_number = val

    @property
    def delivery_terms(self) -> str | None:
        return self.delivery_term

    @delivery_terms.setter
    def delivery_terms(self, val: str | None) -> None:
        self.delivery_term = val

    @property
    def payment_terms(self) -> str | None:
        return self.payment_term

    @payment_terms.setter
    def payment_terms(self, val: str | None) -> None:
        self.payment_term = val

    @property
    def period(self) -> str | None:
        return self.delivery_period

    @period.setter
    def period(self, val: str | None) -> None:
        self.delivery_period = val

    def __repr__(self) -> str:
        return f"<BidSubmission {self.id}>"