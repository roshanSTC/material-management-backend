from datetime import datetime

from app.extensions.database import db


class TechnoCommercialTender(db.Model):
    __tablename__ = "techno_commercial_tenders"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pqb_no = db.Column(db.String(100), nullable=True)
    tender_title = db.Column(db.String(255), nullable=True)
    tender_no = db.Column(db.String(100), nullable=True)
    tender_issue_date = db.Column(db.Date, nullable=True)
    bid_submission_due_date_time = db.Column(db.DateTime, nullable=True)
    bid_opening_date_time = db.Column(db.DateTime, nullable=True)
    tender_fee = db.Column(db.Numeric(15, 2), nullable=True)
    emd = db.Column(db.Numeric(15, 2), nullable=True)
    tender_validity = db.Column(db.String(100), nullable=True)
    remark = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="completed", nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    project = db.relationship(
        "Project",
        back_populates="techno_commercial_tenders",
    )
    items = db.relationship(
        "TechnoCommercialTenderItem",
        back_populates="techno_commercial_tender",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="TechnoCommercialTenderItem.sr_no.asc()",
    )

    def __repr__(self) -> str:
        return f"<TechnoCommercialTender {self.id}: {self.tender_no}>"


class TechnoCommercialTenderItem(db.Model):
    __tablename__ = "techno_commercial_tender_items"

    id = db.Column(db.Integer, primary_key=True)
    techno_commercial_tender_id = db.Column(
        db.Integer,
        db.ForeignKey("techno_commercial_tenders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sr_no = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    material_name = db.Column(db.String(255), nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Numeric(15, 3), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    techno_commercial_tender = db.relationship(
        "TechnoCommercialTender",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<TechnoCommercialTenderItem {self.id}: {self.description}>"

