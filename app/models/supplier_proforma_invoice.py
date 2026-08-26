from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class SupplierProformaInvoice(db.Model):
    __tablename__ = "supplier_proforma_invoices"

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

    order_confirmation_id: Mapped[int | None] = mapped_column(
        ForeignKey("supplier_order_confirmations.id"),
        nullable=True,
        index=True,
    )

    proforma_invoice_number: Mapped[str] = mapped_column(
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

    delivery_date: Mapped[date | None] = mapped_column(
        Date,
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
    order_confirmation = relationship("SupplierOrderConfirmation")

    items = relationship(
        "SupplierProformaInvoiceItem",
        back_populates="proforma_invoice",
        cascade="all, delete-orphan",
    )