from decimal import Decimal

from app.extensions.database import db
from app.models import PurchaseOrder, SupplierInvoice, SupplierPayment
from app.repositories.supplier_payment_repository import (
    create_supplier_payment,
    delete_supplier_payment,
    get_latest_supplier_payment_for_project,
    get_project,
    get_supplier,
    get_supplier_payment,
    get_total_previously_paid,
    list_supplier_payments,
    update_supplier_payment,
)


class SupplierPaymentError(Exception):
    """Base error for supplier payment operations."""


class ProjectNotFoundError(SupplierPaymentError):
    pass


class SupplierNotFoundError(SupplierPaymentError):
    pass


class SupplierPaymentNotFoundError(SupplierPaymentError):
    pass


class PaymentExceedsBalanceError(SupplierPaymentError):
    pass


class TotalSupplierValueRequiredError(SupplierPaymentError):
    pass


def _resolve_total_supplier_value(project_id: int, provided_val: any = None) -> Decimal:
    if provided_val is not None:
        try:
            val = Decimal(str(provided_val))
            if val > Decimal("0.00"):
                return val
        except Exception:
            pass

    # Check previous payment for project
    latest_payment = get_latest_supplier_payment_for_project(project_id)
    if latest_payment and latest_payment.total_supplier_value is not None:
        try:
            val = Decimal(str(latest_payment.total_supplier_value))
            if val > Decimal("0.00"):
                return val
        except Exception:
            pass

    # Check SupplierInvoice for project
    supplier_inv = SupplierInvoice.query.filter_by(project_id=project_id).first()
    if supplier_inv:
        if supplier_inv.total_amount is not None:
            try:
                val = Decimal(str(supplier_inv.total_amount))
                if val > Decimal("0.00"):
                    return val
            except Exception:
                pass
        if supplier_inv.total_net_amount is not None:
            try:
                val = Decimal(str(supplier_inv.total_net_amount))
                if val > Decimal("0.00"):
                    return val
            except Exception:
                pass

    # Check PurchaseOrder for project
    po = PurchaseOrder.query.filter_by(project_id=project_id).first()
    if po:
        if po.total_gross_amount is not None:
            try:
                val = Decimal(str(po.total_gross_amount))
                if val > Decimal("0.00"):
                    return val
            except Exception:
                pass
        if po.total_net_amount is not None:
            try:
                val = Decimal(str(po.total_net_amount))
                if val > Decimal("0.00"):
                    return val
            except Exception:
                pass

    raise TotalSupplierValueRequiredError(
        "Total supplier commitment value is required or could not be determined."
    )


def _calculate_payment_amounts(
    data: dict,
    is_update: bool = False,
    existing_payment: SupplierPayment | None = None,
) -> None:
    project_id = data.get("project_id")
    if project_id is None and existing_payment is not None:
        project_id = existing_payment.project_id

    raw_amount_paid = data.get("amount_paid")
    if raw_amount_paid is None:
        if existing_payment is not None and existing_payment.amount_paid is not None:
            raw_amount_paid = existing_payment.amount_paid
        else:
            return

    try:
        amount_paid = Decimal(str(raw_amount_paid))
    except Exception:
        return

    provided_tsv = data.get("total_supplier_value")
    if provided_tsv is None and existing_payment is not None:
        provided_tsv = existing_payment.total_supplier_value

    total_supplier_value = _resolve_total_supplier_value(project_id, provided_tsv)
    data["total_supplier_value"] = str(total_supplier_value.quantize(Decimal("0.01")))
    data["amount_paid"] = str(amount_paid.quantize(Decimal("0.01")))

    exclude_id = existing_payment.id if existing_payment is not None else None
    total_previously_paid = get_total_previously_paid(project_id, exclude_id=exclude_id)
    remaining_before = total_supplier_value - total_previously_paid

    if amount_paid > remaining_before:
        curr = str(
            data.get("currency")
            or (existing_payment.currency if existing_payment else "INR")
        ).strip().upper()
        symbol = "₹" if curr == "INR" else (f"{curr} " if curr else "₹")
        raise PaymentExceedsBalanceError(
            f"Payment exceeds outstanding balance of {symbol}{remaining_before:.2f}"
        )

    cumulative_paid = total_previously_paid + amount_paid
    pending_amount = (total_supplier_value - cumulative_paid).quantize(Decimal("0.01"))
    if pending_amount < Decimal("0.00"):
        pending_amount = Decimal("0.00")
    data["pending_amount"] = str(pending_amount)

    if total_supplier_value > Decimal("0.00"):
        pct = ((amount_paid / total_supplier_value) * Decimal("100")).quantize(Decimal("0.01"))
        data["payment_percentage"] = str(pct)


def create_supplier_payment_transaction(*, data: dict) -> SupplierPayment:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    supplier_id = data.get("supplier_id")
    if supplier_id is None:
        data["supplier_id"] = project.supplier_id
    else:
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    _calculate_payment_amounts(data, is_update=False)

    payment = create_supplier_payment(data=data)
    db.session.flush()
    return payment


def get_supplier_payment_record(payment_id: int) -> SupplierPayment:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        raise SupplierPaymentNotFoundError(
            f"Supplier payment with ID {payment_id} not found."
        )
    return payment


def list_supplier_payment_records(
    *,
    project_id: int | None = None,
    supplier_id: int | None = None,
    currency: str | None = None,
) -> list[SupplierPayment]:
    return list_supplier_payments(
        project_id=project_id,
        supplier_id=supplier_id,
        currency=currency,
    )


def update_supplier_payment_transaction(
    *,
    payment_id: int,
    data: dict,
) -> SupplierPayment:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        raise SupplierPaymentNotFoundError(
            f"Supplier payment with ID {payment_id} not found."
        )

    if "project_id" in data and data["project_id"] is not None:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    if "supplier_id" in data and data["supplier_id"] is not None:
        supplier_id = data["supplier_id"]
        supplier = get_supplier(supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found.")

    if any(k in data for k in ("amount_paid", "total_supplier_value", "payment_percentage", "pending_amount")):
        _calculate_payment_amounts(data, is_update=True, existing_payment=payment)

    updated_payment = update_supplier_payment(
        payment=payment,
        data=data,
    )
    db.session.flush()
    return updated_payment


def delete_supplier_payment_transaction(payment_id: int) -> list[str]:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        raise SupplierPaymentNotFoundError(
            f"Supplier payment with ID {payment_id} not found."
        )

    storage_keys = delete_supplier_payment(payment_id)
    db.session.flush()
    return storage_keys
