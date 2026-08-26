from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class SupplierInvoice(db.Model):
    __tablename__ = "supplier_invoices"

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

    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    delivery_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    payment_terms: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    warranty_period: Mapped[str | None] = mapped_column(
        String(100),
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
        "SupplierInvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )