from datetime import datetime

from app.extensions.database import db


class QuotationRequest(db.Model):
    __tablename__ = "quotation_requests"

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

    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    quotation_requested_date = db.Column(
        db.Date,
        nullable=False,
    )

    supplier_contacted = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    remarks = db.Column(
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
        back_populates="quotation_requests",
    )

    supplier = db.relationship(
        "Supplier",
        back_populates="quotation_requests",
    )

    items = db.relationship(
        "QuotationRequestItem",
        back_populates="quotation_request",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<QuotationRequest "
            f"{self.id}: "
            f"project={self.project_id} "
            f"supplier={self.supplier_id}>"
        )