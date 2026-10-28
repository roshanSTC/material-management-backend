from datetime import datetime

from app.extensions.database import db


class BidDocumentLte(db.Model):
    __tablename__ = "bid_document_ltes"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_name = db.Column(db.String(255), nullable=True)
    tender_title = db.Column(db.String(255), nullable=True)
    tender_no = db.Column(db.String(100), nullable=True)
    tender_issue_date = db.Column(db.Date, nullable=True)
    total_no_corrigendum_issued = db.Column(db.Integer, default=0, nullable=True)
    bid_submission_date = db.Column(db.Date, nullable=True)
    delivery_terms = db.Column(db.String(100), nullable=True)
    delivery_period = db.Column(db.String(100), nullable=True)
    bid_validity = db.Column(db.String(100), nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True)
    warranty_period = db.Column(db.String(100), nullable=True)
    gst_pct = db.Column(db.Numeric(10, 2), nullable=True)
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
        back_populates="bid_document_ltes",
    )
    items = db.relationship(
        "BidDocumentLteItem",
        back_populates="bid_document_lte",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="BidDocumentLteItem.sr_no.asc()",
    )

    def __repr__(self) -> str:
        return f"<BidDocumentLte {self.id}: {self.tender_no}>"


class BidDocumentLteItem(db.Model):
    __tablename__ = "bid_document_lte_items"

    id = db.Column(db.Integer, primary_key=True)
    bid_document_lte_id = db.Column(
        db.Integer,
        db.ForeignKey("bid_document_ltes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sr_no = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    material_name = db.Column(db.String(255), nullable=True)
    hsn_sac = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.Numeric(15, 3), nullable=True)
    unit_price = db.Column(db.Numeric(15, 2), nullable=True)
    total_amount = db.Column(db.Numeric(15, 2), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    bid_document_lte = db.relationship(
        "BidDocumentLte",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<BidDocumentLteItem {self.id}: {self.description}>"

