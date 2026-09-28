from decimal import Decimal

from app.extensions.database import db
from app.models import (
    BidSubmission,
    CustomerDeliveryInvoice,
    CustomerPayment,
    CustomerQuotation,
    PurchaseOrder,
)
from app.repositories.customer_payment_repository import (
    create_customer_payment,
    delete_customer_payment,
    get_customer_payment,
    get_latest_customer_payment_for_project,
    get_project,
    get_total_previously_paid,
    list_customer_payments,
    update_customer_payment,
)


class CustomerPaymentError(Exception):
    """Base error for customer payment operations."""


class ProjectNotFoundError(CustomerPaymentError):
    pass


class CustomerPaymentNotFoundError(CustomerPaymentError):
    pass


class PaymentExceedsBalanceError(CustomerPaymentError):
    pass


class InvoiceValueRequiredError(CustomerPaymentError):
    pass


def _try_positive_decimal(raw_val) -> Decimal | None:
    if raw_val is None:
        return None
    try:
        val = Decimal(str(raw_val))
        if val > Decimal("0.00"):
            return val
    except Exception:
        pass
    return None


def _resolve_invoice_value(project_id: int, provided_val: any = None) -> Decimal:
    val = _try_positive_decimal(provided_val)
    if val is not None:
        return val

    # 1. Check previous CustomerPayment for project
    latest_payment = get_latest_customer_payment_for_project(project_id)
    if latest_payment:
        val = _try_positive_decimal(latest_payment.invoice_value)
        if val is not None:
            return val

    # 2. Check CustomerDeliveryInvoice for project
    cust_inv = (
        CustomerDeliveryInvoice.query.filter_by(project_id=project_id)
        .order_by(CustomerDeliveryInvoice.id.desc())
        .first()
    )
    if cust_inv:
        val = _try_positive_decimal(cust_inv.net_total)
        if val is not None:
            return val

    # 3. Check PurchaseOrder for project
    po = (
        PurchaseOrder.query.filter_by(project_id=project_id)
        .order_by(PurchaseOrder.id.desc())
        .first()
    )
    if po:
        for candidate in (po.total_gross_amount, po.total_net_amount):
            val = _try_positive_decimal(candidate)
            if val is not None:
                return val

    # 4. Check BidSubmission for project
    bid = (
        BidSubmission.query.filter_by(project_id=project_id)
        .order_by(BidSubmission.id.desc())
        .first()
    )
    if bid and bid.items:
        net_sum = Decimal("0.00")
        for item in bid.items:
            if item.net_total is not None:
                net_sum += Decimal(str(item.net_total))
            elif item.unit_price is not None and item.quantity is not None:
                net_sum += Decimal(str(item.unit_price)) * Decimal(str(item.quantity))
        if net_sum > Decimal("0.00"):
            if bid.gst_rate is not None:
                try:
                    total_val = (
                        net_sum * (Decimal("1.00") + Decimal(str(bid.gst_rate)) / Decimal("100.00"))
                    ).quantize(Decimal("0.01"))
                    val = _try_positive_decimal(total_val)
                except Exception:
                    val = _try_positive_decimal(net_sum)
            else:
                val = _try_positive_decimal(net_sum)
            if val is not None:
                return val

    # 5. Check CustomerQuotation for project
    cust_quote = (
        CustomerQuotation.query.filter_by(project_id=project_id)
        .order_by(CustomerQuotation.id.desc())
        .first()
    )
    if cust_quote:
        for candidate in (cust_quote.total_net_amount, cust_quote.quotation_value):
            val = _try_positive_decimal(candidate)
            if val is not None:
                return val

    raise InvoiceValueRequiredError(
        "Total customer invoice value is required or could not be determined."
    )


def _resolve_invoice_metadata(
    project_id: int,
    data: dict,
    existing_payment: CustomerPayment | None = None,
) -> None:
    inv_no = data.get("invoice_no") or data.get("invoice_number")
    inv_date = data.get("invoice_date")

    if inv_no and inv_date:
        return

    if existing_payment is not None:
        if not inv_no and existing_payment.invoice_no:
            inv_no = existing_payment.invoice_no
        if not inv_date and existing_payment.invoice_date:
            inv_date = existing_payment.invoice_date

    if not inv_no or not inv_date:
        latest_payment = get_latest_customer_payment_for_project(project_id)
        if latest_payment is not None:
            if not inv_no and latest_payment.invoice_no:
                inv_no = latest_payment.invoice_no
            if not inv_date and latest_payment.invoice_date:
                inv_date = latest_payment.invoice_date

    if not inv_no or not inv_date:
        cust_inv = (
            CustomerDeliveryInvoice.query.filter_by(project_id=project_id)
            .order_by(CustomerDeliveryInvoice.id.desc())
            .first()
        )
        if cust_inv is not None:
            if not inv_no and cust_inv.invoice_no:
                inv_no = cust_inv.invoice_no
            if not inv_date and cust_inv.invoice_date:
                inv_date = cust_inv.invoice_date

    if not inv_no or not inv_date:
        po = (
            PurchaseOrder.query.filter_by(project_id=project_id)
            .order_by(PurchaseOrder.id.desc())
            .first()
        )
        if po is not None:
            if not inv_no and po.po_number:
                inv_no = po.po_number
            if not inv_date and po.po_date:
                inv_date = po.po_date

    if not inv_no:
        inv_no = "N/A"
    if not inv_date:
        inv_date = data.get("payment_date")

    if data.get("invoice_no") is None:
        data["invoice_no"] = inv_no
    if data.get("invoice_date") is None and inv_date is not None:
        data["invoice_date"] = inv_date


def _calculate_payment_amounts(
    data: dict,
    is_update: bool = False,
    existing_payment: CustomerPayment | None = None,
) -> None:
    project_id = data.get("project_id")
    if project_id is None and existing_payment is not None:
        project_id = existing_payment.project_id

    provided_iv = data.get("invoice_value")
    if provided_iv is None and existing_payment is not None:
        provided_iv = existing_payment.invoice_value

    invoice_value = _resolve_invoice_value(project_id, provided_iv)
    data["invoice_value"] = str(invoice_value.quantize(Decimal("0.01")))

    raw_payment_amount = data.get("payment_amount")
    raw_pct = data.get("payment_percentage")

    payment_amount = None
    if raw_payment_amount is not None:
        try:
            payment_amount = Decimal(str(raw_payment_amount))
        except Exception:
            payment_amount = None
    elif raw_pct is not None and invoice_value > Decimal("0.00"):
        try:
            pct_dec = Decimal(str(raw_pct))
            payment_amount = ((pct_dec / Decimal("100")) * invoice_value).quantize(
                Decimal("0.01")
            )
        except Exception:
            payment_amount = None
    elif existing_payment is not None and existing_payment.payment_amount is not None:
        try:
            payment_amount = Decimal(str(existing_payment.payment_amount))
        except Exception:
            payment_amount = None

    if payment_amount is None:
        return

    data["payment_amount"] = str(payment_amount.quantize(Decimal("0.01")))

    exclude_id = existing_payment.id if existing_payment is not None else None
    total_previously_paid = get_total_previously_paid(project_id, exclude_id=exclude_id)
    remaining_before = (invoice_value - total_previously_paid).quantize(Decimal("0.01"))

    if payment_amount > remaining_before:
        symbol = "₹"
        if remaining_before <= Decimal("0.00"):
            raise PaymentExceedsBalanceError(
                f"Payment is already 100% completed. Payment exceeds outstanding balance of {symbol}0.00"
            )
        raise PaymentExceedsBalanceError(
            f"Payment exceeds outstanding balance of {symbol}{remaining_before:.2f}"
        )

    cumulative_paid = total_previously_paid + payment_amount
    pending_amount = (invoice_value - cumulative_paid).quantize(Decimal("0.01"))
    if pending_amount < Decimal("0.00"):
        pending_amount = Decimal("0.00")
    data["pending_amount"] = str(pending_amount)

    if invoice_value > Decimal("0.00"):
        pct = ((payment_amount / invoice_value) * Decimal("100")).quantize(Decimal("0.01"))
        data["payment_percentage"] = str(pct)


def _recalculate_project_payments(
    project_id: int,
    override_iv: Decimal | None = None,
) -> None:
    payments = list_customer_payments(project_id=project_id, latest_first=False)
    if not payments:
        return

    iv = _try_positive_decimal(override_iv)
    if iv is None:
        for p in reversed(payments):
            iv = _try_positive_decimal(p.invoice_value)
            if iv is not None:
                break
    if iv is None:
        try:
            iv = _resolve_invoice_value(project_id)
        except InvoiceValueRequiredError:
            return

    iv = iv.quantize(Decimal("0.01"))
    running_paid = Decimal("0.00")
    for p in payments:
        amt = Decimal(str(p.payment_amount or 0)).quantize(Decimal("0.01"))
        running_paid += amt
        p.invoice_value = iv
        if iv > Decimal("0.00"):
            p._payment_percentage = ((amt / iv) * Decimal("100")).quantize(Decimal("0.01"))
            pend = (iv - running_paid).quantize(Decimal("0.01"))
            p._pending_amount = pend if pend > Decimal("0.00") else Decimal("0.00")
            p._cumulative_paid = running_paid


def get_customer_payment_summary(project_id: int) -> dict:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    payments = list_customer_payments(project_id=project_id, latest_first=False)
    iv = Decimal("0.00")
    try:
        iv = _resolve_invoice_value(project_id).quantize(Decimal("0.01"))
    except InvoiceValueRequiredError:
        iv = Decimal("0.00")

    total_paid = sum(
        (Decimal(str(p.payment_amount or 0)) for p in payments),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))

    if iv > Decimal("0.00"):
        pending_amt = max((iv - total_paid).quantize(Decimal("0.01")), Decimal("0.00"))
        paid_pct = min(
            ((total_paid / iv) * Decimal("100")).quantize(Decimal("0.01")),
            Decimal("100.00"),
        )
        pending_pct = max((Decimal("100.00") - paid_pct).quantize(Decimal("0.01")), Decimal("0.00"))
        is_completed = (pending_amt <= Decimal("0.00")) or (paid_pct >= Decimal("100.00"))
    else:
        pending_amt = Decimal("0.00")
        paid_pct = Decimal("100.00") if total_paid > Decimal("0.00") else Decimal("0.00")
        pending_pct = Decimal("0.00") if total_paid > Decimal("0.00") else Decimal("100.00")
        is_completed = total_paid > Decimal("0.00")

    if is_completed:
        payment_status = "completed"
        status_message = "Payment completed"
    elif total_paid > Decimal("0.00"):
        payment_status = "partial"
        status_message = f"{paid_pct:.2f}% paid, {pending_pct:.2f}% pending"
    else:
        payment_status = "pending"
        status_message = "0.00% paid, 100.00% pending"

    latest = payments[-1] if payments else None
    inv_no = latest.invoice_no if latest else None
    inv_date = latest.invoice_date if latest else None
    if not inv_no or not inv_date:
        cust_inv = (
            CustomerDeliveryInvoice.query.filter_by(project_id=project_id)
            .order_by(CustomerDeliveryInvoice.id.desc())
            .first()
        )
        if cust_inv:
            if not inv_no:
                inv_no = cust_inv.invoice_no
            if not inv_date:
                inv_date = cust_inv.invoice_date

    return {
        "project_id": project_id,
        "customer_id": project.customer_id,
        "invoice_no": inv_no,
        "invoice_number": inv_no,
        "invoice_date": inv_date,
        "invoice_value": f"{iv:.2f}",
        "total_paid_amount": f"{total_paid:.2f}",
        "pending_amount": f"{pending_amt:.2f}",
        "cumulative_payment_percentage": f"{paid_pct:.2f}",
        "pending_percentage": f"{pending_pct:.2f}",
        "is_payment_completed": is_completed,
        "payment_status": payment_status,
        "payment_status_message": status_message,
        "payment_count": len(payments),
    }


def create_customer_payment_transaction(
    *, data: dict, user_id: int | None = None
) -> CustomerPayment:
    project_id = data.get("project_id")
    if not project_id:
        raise ProjectNotFoundError("Project ID is required.")

    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    _resolve_invoice_metadata(project_id, data)
    _calculate_payment_amounts(data, is_update=False)

    payment = create_customer_payment(data=data)
    db.session.flush()

    _recalculate_project_payments(
        project_id,
        override_iv=_try_positive_decimal(data.get("invoice_value")),
    )
    db.session.flush()

    remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=14,
        remarks_data=remarks_val,
        default_user_id=user_id,
        entity_id=payment.id,
    )

    from app.services.project_step_service import sync_customer_payment_step
    sync_customer_payment_step(project_id)

    return payment


def get_customer_payment_record(payment_id: int) -> CustomerPayment:
    payment = get_customer_payment(payment_id)
    if payment is None:
        raise CustomerPaymentNotFoundError(
            f"Customer payment with ID {payment_id} not found."
        )
    return payment


def list_customer_payment_records(
    *,
    project_id: int | None = None,
    invoice_no: str | None = None,
) -> list[CustomerPayment]:
    payments = list_customer_payments(
        project_id=project_id,
        invoice_no=invoice_no,
        latest_first=True,
    )
    if not invoice_no and payments:
        by_project: dict[int, list[CustomerPayment]] = {}
        for p in payments:
            by_project.setdefault(p.project_id, []).append(p)
        for pid, proj_payments in by_project.items():
            chronological = sorted(
                proj_payments,
                key=lambda x: (x.payment_date, x.id),
            )
            iv = Decimal("0.00")
            for p in reversed(chronological):
                cand = _try_positive_decimal(p.invoice_value)
                if cand is not None:
                    iv = cand.quantize(Decimal("0.01"))
                    break
            running_paid = Decimal("0.00")
            for p in chronological:
                amt = Decimal(str(p.payment_amount or 0)).quantize(Decimal("0.01"))
                running_paid += amt
                p._cumulative_paid = running_paid
                if iv > Decimal("0.00"):
                    p._payment_percentage = ((amt / iv) * Decimal("100")).quantize(Decimal("0.01"))
                    pend = (iv - running_paid).quantize(Decimal("0.01"))
                    p._pending_amount = pend if pend > Decimal("0.00") else Decimal("0.00")
                else:
                    p._payment_percentage = Decimal("100.00") if amt > Decimal("0.00") else Decimal("0.00")
                    p._pending_amount = Decimal("0.00")
    return payments


def update_customer_payment_transaction(
    *,
    payment_id: int,
    data: dict,
    user_id: int | None = None,
) -> CustomerPayment:
    payment = get_customer_payment(payment_id)
    if payment is None:
        raise CustomerPaymentNotFoundError(
            f"Customer payment with ID {payment_id} not found."
        )
    previous_project_id = payment.project_id

    if "project_id" in data and data["project_id"] is not None:
        project_id = data["project_id"]
        project = get_project(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    if any(
        k in data
        for k in (
            "payment_amount",
            "invoice_value",
            "payment_percentage",
            "pending_amount",
        )
    ):
        _calculate_payment_amounts(data, is_update=True, existing_payment=payment)

    updated_payment = update_customer_payment(
        payment=payment,
        data=data,
    )
    db.session.flush()

    _recalculate_project_payments(
        updated_payment.project_id,
        override_iv=_try_positive_decimal(data.get("invoice_value"))
        or _try_positive_decimal(updated_payment.invoice_value),
    )
    if updated_payment.project_id != previous_project_id:
        _recalculate_project_payments(previous_project_id)
    db.session.flush()

    if "remarks" in data or "remark" in data:
        remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
        from app.services.step_remark_service import sync_step_remarks
        sync_step_remarks(
            project_id=updated_payment.project_id,
            step_number=14,
            remarks_data=remarks_val,
            default_user_id=user_id,
            entity_id=updated_payment.id,
        )

    from app.services.project_step_service import sync_customer_payment_step
    sync_customer_payment_step(updated_payment.project_id)
    if updated_payment.project_id != previous_project_id:
        sync_customer_payment_step(previous_project_id)

    return updated_payment


def delete_customer_payment_transaction(payment_id: int) -> list[str]:
    payment = get_customer_payment(payment_id)
    if payment is None:
        raise CustomerPaymentNotFoundError(
            f"Customer payment with ID {payment_id} not found."
        )

    project_id = payment.project_id
    storage_keys = delete_customer_payment(payment_id)
    db.session.flush()

    _recalculate_project_payments(project_id)
    db.session.flush()

    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=14,
        remarks_data=None,
        entity_id=payment_id,
    )

    from app.services.project_step_service import sync_customer_payment_step
    sync_customer_payment_step(project_id)

    return storage_keys

