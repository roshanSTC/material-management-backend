from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class SupplierPackingListItem(db.Model):
    __tablename__ = "supplier_packing_list_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    packing_list_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_packing_lists.id"),
        nullable=False,
        index=True,
    )

    material_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 3),
        nullable=False,
    )

    unit_weight_kg: Mapped[Decimal] = mapped_column(
        Numeric(18, 3),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    packing_list = relationship(
        "SupplierPackingList",
        back_populates="items",
    )