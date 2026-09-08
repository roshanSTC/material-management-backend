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

    cha_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    bill_of_entry_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    boe_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    customs_location: Mapped[str | None] = mapped_column(
        String(255),
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

    cfs_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    transaction_ref_no: Mapped[str | None] = mapped_column(
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

    total_customs_amount: Mapped[Decimal | None] = mapped_column(
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

    # Compatibility properties
    @property
    def customs_location_port(self) -> str | None:
        return self.customs_location

    @customs_location_port.setter
    def customs_location_port(self, value: str | None) -> None:
        self.customs_location = value

    @property
    def challan_number(self) -> str | None:
        return self.challan_no

    @challan_number.setter
    def challan_number(self, value: str | None) -> None:
        self.challan_no = value

    @property
    def transaction_payment_reference(self) -> str | None:
        return self.transaction_ref_no

    @transaction_payment_reference.setter
    def transaction_payment_reference(self, value: str | None) -> None:
        self.transaction_ref_no = value

    @property
    def bill_of_entry_number(self) -> str | None:
        return self.bill_of_entry_no

    @bill_of_entry_number.setter
    def bill_of_entry_number(self, value: str | None) -> None:
        self.bill_of_entry_no = value