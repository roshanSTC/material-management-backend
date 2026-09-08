from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class ImportLogistics(db.Model):
    __tablename__ = "import_logistics"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=True,
        index=True,
    )

    logistic_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    port_of_discharge: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remark: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Air transport fields
    airway_bill_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    flight_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    flight_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    airport_of_loading: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Sea transport fields
    bill_of_lading_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    vessel_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    voyage_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    port_of_loading: Mapped[str | None] = mapped_column(
        String(255),
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
    supplier = relationship("Supplier")

    # Compatibility properties
    @property
    def airway_bill_number(self) -> str | None:
        return self.airway_bill_no

    @airway_bill_number.setter
    def airway_bill_number(self, value: str | None) -> None:
        self.airway_bill_no = value

    @property
    def flight_number(self) -> str | None:
        return self.flight_no

    @flight_number.setter
    def flight_number(self, value: str | None) -> None:
        self.flight_no = value

    @property
    def logistics_date(self) -> date:
        return self.date

    @logistics_date.setter
    def logistics_date(self, value: date) -> None:
        self.date = value