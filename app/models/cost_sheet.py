from datetime import datetime

from app.extensions.database import db


class CostSheet(db.Model):
    __tablename__ = "cost_sheets"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    version_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    global_params = db.Column(db.JSON, nullable=False)
    output = db.Column(db.JSON, nullable=False, default=dict)
    status = db.Column(db.String(20), nullable=False, default="Draft")
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    project = db.relationship("Project", back_populates="cost_sheets")
    creator = db.relationship("User", foreign_keys=[created_by], lazy="select")
    items = db.relationship(
        "CostSheetItem",
        back_populates="cost_sheet",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="CostSheetItem.id",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "project_id",
            "version_number",
            name="uq_cost_sheets_project_version",
        ),
        db.CheckConstraint(
            "status IN ('Draft', 'Approved', 'Archived')",
            name="ck_cost_sheets_status",
        ),
        db.CheckConstraint(
            "version_number > 0",
            name="ck_cost_sheets_version_number",
        ),
    )

    def __repr__(self) -> str:
        return f"<CostSheet {self.id}: project={self.project_id} v{self.version_number}>"
