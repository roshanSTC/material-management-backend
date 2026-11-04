from datetime import datetime

from app.extensions.database import db


class InternationalCompetitiveBidding(db.Model):
    __tablename__ = "international_competitive_biddings"

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
    form_code = db.Column(db.String(100), default="FORM_35_ICB", nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    project = db.relationship(
        "Project",
        back_populates="international_competitive_biddings",
    )
    items = db.relationship(
        "InternationalCompetitiveBiddingItem",
        back_populates="international_competitive_bidding",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="InternationalCompetitiveBiddingItem.sr_no.asc()",
    )

    @property
    def icb_no(self):
        return self.tender_no

    @icb_no.setter
    def icb_no(self, val):
        self.tender_no = val

    @property
    def tender_number(self):
        return self.tender_no

    @tender_number.setter
    def tender_number(self, val):
        self.tender_no = val

    @property
    def tender_enquiry_no(self):
        return self.tender_no

    @tender_enquiry_no.setter
    def tender_enquiry_no(self, val):
        self.tender_no = val

    @property
    def pqb_number(self):
        return self.pqb_no

    @pqb_number.setter
    def pqb_number(self, val):
        self.pqb_no = val

    @property
    def validity(self):
        return self.tender_validity

    @validity.setter
    def validity(self, val):
        self.tender_validity = val

    @property
    def remarks(self):
        return self.remark

    @remarks.setter
    def remarks(self, val):
        self.remark = val

    def __repr__(self) -> str:
        return f"<InternationalCompetitiveBidding {self.id}: {self.tender_no}>"


class InternationalCompetitiveBiddingItem(db.Model):
    __tablename__ = "international_competitive_bidding_items"

    id = db.Column(db.Integer, primary_key=True)
    international_competitive_bidding_id = db.Column(
        db.Integer,
        db.ForeignKey("international_competitive_biddings.id", ondelete="CASCADE"),
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

    international_competitive_bidding = db.relationship(
        "InternationalCompetitiveBidding",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<InternationalCompetitiveBiddingItem {self.id}: {self.description}>"

