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

    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=False,
        index=True,
    )

    logistic_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    airway_bill_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    logistics_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    flight_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    flight_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    airport_of_loading: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    port_of_discharge: Mapped[str | None] = mapped_column(
        String(255),
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
    supplier = relationship("Supplier")