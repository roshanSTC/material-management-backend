from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class BillOfEntry(db.Model):
    __tablename__ = "bills_of_entry"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    logistic_mode: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    shipment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    awb_bl_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    flight_vessel_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    flight_vessel_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    port_loading: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    port_discharge: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    bill_of_entry_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    boe_filing_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    total_assessable_value: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    basic_custom_duty_bcd: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    sws: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    igst: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    duty_paid_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    challan_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    payment_ref_no: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    customs_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    cfs_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    total_duty: Mapped[Decimal | None] = mapped_column(
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
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    project = relationship("Project")