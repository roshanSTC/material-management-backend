from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class CustomsClearance(db.Model):
    __tablename__ = "customs_clearances"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    bill_of_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("bills_of_entry.id"),
        nullable=True,
        index=True,
    )

    freight_forwarder_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    cha_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    invoice_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    invoice_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    invoice_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    payment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    payment_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    project = relationship("Project")
    bill_of_entry = relationship("BillOfEntry")
    items = relationship(
        "CustomsClearanceItem",
        back_populates="customs_clearance",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="CustomsClearanceItem.sr_no.asc()",
    )


class CustomsClearanceItem(db.Model):
    __tablename__ = "customs_clearance_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    customs_clearance_id: Mapped[int] = mapped_column(
        ForeignKey("customs_clearances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sr_no: Mapped[int | None] = mapped_column(nullable=True)

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    customs_clearance = relationship("CustomsClearance", back_populates="items")