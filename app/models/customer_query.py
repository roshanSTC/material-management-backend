from datetime import date, datetime

from app.extensions.database import db


class CustomerQuery(db.Model):
    __tablename__ = "customer_queries"

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

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    qo_date = db.Column(
        db.Date,
        nullable=False,
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
        back_populates="customer_queries",
    )

    customer = db.relationship(
        "Customer",
        back_populates="customer_queries",
    )

    items = db.relationship(
        "CustomerQueryItem",
        back_populates="customer_query",
        cascade="all, delete-orphan",
        lazy="select",
    )
    
    attachments = db.relationship(
        "Attachment",
        back_populates="customer_query",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<CustomerQuery {self.id}>"