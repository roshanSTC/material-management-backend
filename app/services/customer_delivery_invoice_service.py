from decimal import Decimal

from app.extensions.database import db
from app.models import CustomerDeliveryInvoice
from app.repositories.customer_delivery_invoice_repository import (
    create_customer_delivery_invoice,
    delete_customer_delivery_invoice,
    get_customer_delivery_invoice,
    get_project,
    list_customer_delivery_invoices,
    update_customer_delivery_invoice,
)


class CustomerDeliveryInvoiceError(Exception):
    """Base error for customer delivery invoice operations."""


class ProjectNotFoundError(CustomerDeliveryInvoiceError):
    pass


class CustomerDeliveryInvoiceNotFoundError(CustomerDeliveryInvoiceError):
    pass


def _calculate_amounts(data: dict) -> None:
    items = data.get("items") or []
    item_net_sum = Decimal("0.00")

    for item in items:
        qty = item.get("quantity")
        unit_price = item.get("unit_price")
        net_amt = item.get("net_amount")

        if net_amt is None and qty is not None and unit_price is not None:
            try:
                computed_net = (Decimal(str(qty)) * Decimal(str(unit_price))).quantize(
                    Decimal("0.01")
                )
                item["net_amount"] = str(computed_net)
                item_net_sum += computed_net
            except Exception:
                pass
        elif net_amt is not None:
            try:
                item_net_sum += Decimal(str(net_amt))
            except Exception:
                pass

    gst_rate = data.get("gst_rate")
    gst_amount = data.get("gst_amount")
    if gst_amount is None and gst_rate is not None and item_net_sum > 0:
        try:
            computed_gst = (
                item_net_sum * Decimal(str(gst_rate)) / Decimal("100")
            ).quantize(Decimal("0.01"))
            data["gst_amount"] = str(computed_gst)
        except Exception:
            pass

    net_total = data.get("net_total")
    if net_total is None and item_net_sum > 0:
        try:
            gst_val = Decimal(str(data.get("gst_amount") or 0))
            round_val = Decimal(str(data.get("round_off") or 0))
            data["net_total"] = str(
                (item_net_sum + gst_val + round_val).quantize(Decimal("0.01"))
            )
        except Exception:
            pass


def create_customer_delivery_invoice_transaction(*, data: dict) -> CustomerDeliveryInvoice:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    _calculate_amounts(data)

    invoice = create_customer_delivery_invoice(data=data)
    db.session.flush()

    return invoice


def get_customer_delivery_invoice_record(invoice_id: int) -> CustomerDeliveryInvoice:
    invoice = get_customer_delivery_invoice(invoice_id)
    if invoice is None:
        raise CustomerDeliveryInvoiceNotFoundError(
            f"Customer delivery invoice with ID {invoice_id} not found."
        )
    return invoice


def list_customer_delivery_invoice_records(
    *,
    project_id: int | None = None,
    invoice_no: str | None = None,
) -> list[CustomerDeliveryInvoice]:
    return list_customer_delivery_invoices(
        project_id=project_id,
        invoice_no=invoice_no,
    )


def update_customer_delivery_invoice_transaction(
    *,
    invoice_id: int,
    data: dict,
) -> CustomerDeliveryInvoice:
    invoice = get_customer_delivery_invoice(invoice_id)
    if invoice is None:
        raise CustomerDeliveryInvoiceNotFoundError(
            f"Customer delivery invoice with ID {invoice_id} not found."
        )

    if "project_id" in data:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    if "items" in data:
        _calculate_amounts(data)

    updated_invoice = update_customer_delivery_invoice(
        invoice=invoice,
        data=data,
    )
    db.session.flush()

    return updated_invoice


def delete_customer_delivery_invoice_transaction(invoice_id: int) -> list[str]:
    invoice = get_customer_delivery_invoice(invoice_id)
    if invoice is None:
        raise CustomerDeliveryInvoiceNotFoundError(
            f"Customer delivery invoice with ID {invoice_id} not found."
        )

    storage_keys = delete_customer_delivery_invoice(invoice_id)
    db.session.flush()
    return storage_keys

