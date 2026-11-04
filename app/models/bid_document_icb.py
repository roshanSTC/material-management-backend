from datetime import datetime

from app.extensions.database import db


class BidDocumentIcb(db.Model):
    __tablename__ = "bid_document_icbs"

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
    form_code = db.Column(db.String(100), default="FORM_36_BID_DOC_ICB", nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    project = db.relationship(
        "Project",
        back_populates="bid_document_icbs",
    )
    items = db.relationship(
        "BidDocumentIcbItem",
        back_populates="bid_document_icb",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="BidDocumentIcbItem.sr_no.asc()",
    )

    @property
    def tender_number(self):
        return self.tender_no

    @tender_number.setter
    def tender_number(self, val):
        self.tender_no = val

    @property
    def delivery_term(self):
        return self.delivery_terms

    @delivery_term.setter
    def delivery_term(self, val):
        self.delivery_terms = val

    @property
    def payment_term(self):
        return self.payment_terms

    @payment_term.setter
    def payment_term(self, val):
        self.payment_terms = val

    @property
    def gst_rate(self):
        return self.gst_pct

    @gst_rate.setter
    def gst_rate(self, val):
        self.gst_pct = val

    @property
    def gst_rate_pct(self):
        return self.gst_pct

    @gst_rate_pct.setter
    def gst_rate_pct(self, val):
        self.gst_pct = val

    @property
    def total_corrigendum_issued(self):
        return self.total_no_corrigendum_issued

    @total_corrigendum_issued.setter
    def total_corrigendum_issued(self, val):
        self.total_no_corrigendum_issued = val

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, val):
        self.remark = val

    def __repr__(self) -> str:
        return f"<BidDocumentIcb {self.id}: {self.tender_no}>"


class BidDocumentIcbItem(db.Model):
    __tablename__ = "bid_document_icb_items"

    id = db.Column(db.Integer, primary_key=True)
    bid_document_icb_id = db.Column(
        db.Integer,
        db.ForeignKey("bid_document_icbs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sr_no = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    material_name = db.Column(db.String(255), nullable=True)
    item_code = db.Column(db.String(100), nullable=True)
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

    bid_document_icb = db.relationship(
        "BidDocumentIcb",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<BidDocumentIcbItem {self.id}: {self.description}>"

