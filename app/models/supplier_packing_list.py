from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class SupplierPackingList(db.Model):
    __tablename__ = "supplier_packing_lists"

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

    packing_list_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    packing_list_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    packing_condition: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    total_gross_weight_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 3),
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

    items = relationship(
        "SupplierPackingListItem",
        back_populates="packing_list",
        cascade="all, delete-orphan",
    )