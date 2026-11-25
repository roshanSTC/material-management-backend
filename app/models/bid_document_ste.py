from datetime import datetime

from app.extensions.database import db


class BidDocumentSte(db.Model):
    __tablename__ = "bid_document_stes"

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
    total_net_amount = db.Column(db.Numeric(15, 2), nullable=True)
    total_gross_amount = db.Column(db.Numeric(15, 2), nullable=True)
    gst_amount = db.Column(db.Numeric(15, 2), nullable=True)
    total_amount = db.Column(db.Numeric(15, 2), nullable=True)
    remark = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="completed", nullable=True)
    form_code = db.Column(db.String(100), default="FORM_34_BID_DOC_STE", nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    project = db.relationship(
        "Project",
        back_populates="bid_document_stes",
    )
    items = db.relationship(
        "BidDocumentSteItem",
        back_populates="bid_document_ste",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="BidDocumentSteItem.sr_no.asc()",
    )

    def __repr__(self) -> str:
        return f"<BidDocumentSte {self.id}: {self.tender_no}>"


class BidDocumentSteItem(db.Model):
    __tablename__ = "bid_document_ste_items"

    id = db.Column(db.Integer, primary_key=True)
    bid_document_ste_id = db.Column(
        db.Integer,
        db.ForeignKey("bid_document_stes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sr_no = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
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

    bid_document_ste = db.relationship(
        "BidDocumentSte",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<BidDocumentSteItem {self.id}: {self.description}>"

