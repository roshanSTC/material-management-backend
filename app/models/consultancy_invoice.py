from datetime import datetime

from app.extensions.database import db


class ConsultancyInvoice(db.Model):
    __tablename__ = "consultancy_invoices"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_no = db.Column(
        db.String(100),
        nullable=False,
    )
    invoice_date = db.Column(
        db.Date,
        nullable=True,
    )
    party_name = db.Column(
        db.String(255),
        nullable=True,
    )
    invoice_reference = db.Column(
        db.String(255),
        nullable=True,
    )
    total_value_eur = db.Column(
        db.Numeric(15, 2),
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
        back_populates="consultancy_invoices",
    )

    def __repr__(self) -> str:
        return f"<ConsultancyInvoice {self.id}: {self.invoice_no}>"

