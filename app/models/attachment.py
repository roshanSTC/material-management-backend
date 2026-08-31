from datetime import datetime

from app.extensions.database import db


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    customer_query_id = db.Column(
        db.Integer,
        db.ForeignKey("customer_queries.id"),
        nullable=False,
        index=True,
    )

    file_name = db.Column(
        db.String(255),
        nullable=False,
    )

    storage_key = db.Column(
        db.String(1024),
        nullable=False,
        unique=True,
    )

    content_type = db.Column(
        db.String(100),
        nullable=False,
    )

    file_size = db.Column(
        db.BigInteger,
        nullable=False,
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
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

    customer_query = db.relationship(
        "CustomerQuery",
        back_populates="attachments",
    )

    uploader = db.relationship(
        "User",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Attachment {self.id}: "
            f"customer_query={self.customer_query_id} "
            f"{self.file_name}>"
        )