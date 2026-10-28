from datetime import datetime

from app.extensions.database import db


class PqbBidDocument(db.Model):
    __tablename__ = "pqb_bid_documents"

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
    pqb_title = db.Column(
        db.String(255),
        nullable=True,
    )
    pqb_no = db.Column(
        db.String(100),
        nullable=False,
    )
    pqb_issue_date = db.Column(
        db.Date,
        nullable=True,
    )
    pqb_closing_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    pqb_opening_date_time = db.Column(
        db.DateTime,
        nullable=True,
    )
    total_corrigendum_issued = db.Column(
        db.Integer,
        default=0,
        nullable=True,
    )
    remark = db.Column(
        db.Text,
        nullable=True,
    )
    status = db.Column(
        db.String(30),
        default="completed",
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
        back_populates="pqb_bid_documents",
    )
    items = db.relationship(
        "PqbBidDocumentItem",
        back_populates="pqb_bid_document",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="PqbBidDocumentItem.sr_no.asc()",
    )

    @property
    def total_no_corrigendum_issued(self):
        return self.total_corrigendum_issued

    @total_no_corrigendum_issued.setter
    def total_no_corrigendum_issued(self, value):
        self.total_corrigendum_issued = value

    def __repr__(self) -> str:
        return f"<PqbBidDocument {self.id}: {self.pqb_no}>"


class PqbBidDocumentItem(db.Model):
    __tablename__ = "pqb_bid_document_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    pqb_bid_document_id = db.Column(
        db.Integer,
        db.ForeignKey("pqb_bid_documents.id", ondelete="CASCADE"),
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

    pqb_bid_document = db.relationship(
        "PqbBidDocument",
        back_populates="items",
    )

    def __repr__(self) -> str:
        return f"<PqbBidDocumentItem {self.id}: {self.description}>"
