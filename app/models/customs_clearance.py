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

    bill_of_entry_id: Mapped[int] = mapped_column(
        ForeignKey("bills_of_entry.id"),
        nullable=False,
        index=True,
    )

    cha_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    customs_location_port: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    duty_paid_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    challan_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    cfs_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    transaction_payment_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    duty_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    igst_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    other_customs_charges: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    project = relationship("Project")
    bill_of_entry = relationship("BillOfEntry")