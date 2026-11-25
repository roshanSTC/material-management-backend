from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
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

    transportation_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    lr_rr_awb_no: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    lr_rr_awb_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    from_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    to_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    total_transportation_charges: Mapped[Decimal | None] = mapped_column(
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
    supplier = relationship("Supplier")