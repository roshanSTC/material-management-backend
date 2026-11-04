from datetime import datetime

from app.extensions.database import db


class Corrigendum(db.Model):
    __tablename__ = "corrigendums"

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
    corrigendum_no = db.Column(
        db.String(100),
        nullable=False,
    )
    against_tender_no = db.Column(
        db.String(100),
        nullable=True,
    )
    tender_title = db.Column(
        db.String(255),
        nullable=True,
    )
    issue_date = db.Column(
        db.Date,
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
        back_populates="corrigendums",
    )
    items = db.relationship(
        "CorrigendumItem",
        back_populates="corrigendum",
        cascade="all, delete-orphan",
        order_by="CorrigendumItem.sr_no.asc(), CorrigendumItem.id.asc()",
    )

    # Aliases for frontend compatibility
    @property
    def against_ref_no(self):
        return self.against_tender_no

    @against_ref_no.setter
    def against_ref_no(self, val):
        self.against_tender_no = val

    @property
    def ref_title(self):
        return self.tender_title

    @ref_title.setter
    def ref_title(self, val):
        self.tender_title = val

    def __repr__(self) -> str:
        return f"<Corrigendum {self.id}: {self.corrigendum_no}>"


class CorrigendumItem(db.Model):
    __tablename__ = "corrigendum_items"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    corrigendum_id = db.Column(
        db.Integer,
        db.ForeignKey("corrigendums.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sr_no = db.Column(
        db.Integer,
        nullable=True,
    )
    as_per_tender_doc = db.Column(
        db.Text,
        nullable=True,
    )
    as_per_corrigendum = db.Column(
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

    corrigendum = db.relationship(
        "Corrigendum",
        back_populates="items",
    )

    @property
    def description(self):
        return self.as_per_corrigendum or self.as_per_tender_doc or ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "corrigendum_id": self.corrigendum_id,
            "sr_no": self.sr_no,
            "as_per_tender_doc": self.as_per_tender_doc,
            "as_per_corrigendum": self.as_per_corrigendum,
        }

    def __repr__(self) -> str:
        return f"<CorrigendumItem {self.id}: sr_no={self.sr_no}>"
