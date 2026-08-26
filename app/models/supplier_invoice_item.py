from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class SupplierInvoiceItem(db.Model):
    __tablename__ = "supplier_invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    supplier_invoice_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_invoices.id"),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    hsn_sac: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 3),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    invoice = relationship(
        "SupplierInvoice",
        back_populates="items",
    )