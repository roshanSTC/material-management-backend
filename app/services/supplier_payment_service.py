from decimal import Decimal

from app.extensions.database import db
from app.models import (
    PurchaseOrder,
    SupplierInvoice,
    SupplierOrderConfirmation,
    SupplierPayment,
    SupplierProformaInvoice,
    SupplierQuotation,
)
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


def _resolve_total_supplier_value(project_id: int, provided_val: any = None) -> Decimal:
    val = _try_positive_decimal(provided_val)
    if val is not None:
        return val

    # 1. Check previous payment for project
    latest_payment = get_latest_supplier_payment_for_project(project_id)
    if latest_payment:
        val = _try_positive_decimal(latest_payment.total_supplier_value)
        if val is not None:
            return val

    # 2. Check SupplierInvoice for project
    supplier_inv = (
        SupplierInvoice.query.filter_by(project_id=project_id)
        .order_by(SupplierInvoice.id.desc())
        .first()
    )
    if supplier_inv:
        for candidate in (supplier_inv.total_amount, supplier_inv.total_net_amount):
            val = _try_positive_decimal(candidate)
            if val is not None:
                return val

    # 3. Check SupplierProformaInvoice for project
    proforma_inv = (
        SupplierProformaInvoice.query.filter_by(project_id=project_id)
        .order_by(SupplierProformaInvoice.id.desc())
        .first()
    )
    if proforma_inv:
        for candidate in (proforma_inv.total_amount, proforma_inv.total_net_amount):
            val = _try_positive_decimal(candidate)
            if val is not None:
                return val

    # 4. Check SupplierOrderConfirmation for project
    order_conf = (
        SupplierOrderConfirmation.query.filter_by(project_id=project_id)
        .order_by(SupplierOrderConfirmation.id.desc())
        .first()
    )
    if order_conf:
        for candidate in (order_conf.total_amount, order_conf.total_net_amount):
            val = _try_positive_decimal(candidate)
            if val is not None:
                return val

    # 5. Check PurchaseOrder for project
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

    # 6. Check SupplierQuotation for project
    supp_quote = (
        SupplierQuotation.query.filter_by(project_id=project_id)
        .order_by(SupplierQuotation.id.desc())
        .first()
    )
    if supp_quote:
        val = _try_positive_decimal(supp_quote.quotation_value)
        if val is not None:
            return val

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

    provided_tsv = data.get("total_supplier_value")
    if provided_tsv is None and existing_payment is not None:
        provided_tsv = existing_payment.total_supplier_value

    total_supplier_value = _resolve_total_supplier_value(project_id, provided_tsv)
    data["total_supplier_value"] = str(total_supplier_value.quantize(Decimal("0.01")))

    raw_amount_paid = data.get("amount_paid")
    raw_pct = data.get("payment_percentage")

    amount_paid = None
    if raw_amount_paid is not None:
        try:
            amount_paid = Decimal(str(raw_amount_paid))
        except Exception:
            amount_paid = None
    elif raw_pct is not None and total_supplier_value > Decimal("0.00"):
        try:
            pct_dec = Decimal(str(raw_pct))
            amount_paid = ((pct_dec / Decimal("100")) * total_supplier_value).quantize(
                Decimal("0.01")
            )
        except Exception:
            amount_paid = None
    elif existing_payment is not None and existing_payment.amount_paid is not None:
        try:
            amount_paid = Decimal(str(existing_payment.amount_paid))
        except Exception:
            amount_paid = None

    if amount_paid is None:
        return

    data["amount_paid"] = str(amount_paid.quantize(Decimal("0.01")))

    exclude_id = existing_payment.id if existing_payment is not None else None
    total_previously_paid = get_total_previously_paid(project_id, exclude_id=exclude_id)
    remaining_before = (total_supplier_value - total_previously_paid).quantize(Decimal("0.01"))

    if amount_paid > remaining_before:
        curr = str(
            data.get("currency")
            or (existing_payment.currency if existing_payment else "INR")
        ).strip().upper()
        symbol = "₹" if curr == "INR" else (f"{curr} " if curr else "₹")
        if remaining_before <= Decimal("0.00"):
            raise PaymentExceedsBalanceError(
                f"Payment is already 100% completed. Payment exceeds outstanding balance of {symbol}0.00"
            )
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

    raw_ex_rate = data.get("exchange_rate")
    if raw_ex_rate is None and existing_payment is not None:
        raw_ex_rate = existing_payment.exchange_rate

    raw_twe = data.get("total_with_exchange")
    if raw_twe is None and raw_ex_rate is not None:
        try:
            ex_dec = Decimal(str(raw_ex_rate))
            data["total_with_exchange"] = str((amount_paid * ex_dec).quantize(Decimal("0.01")))
            raw_twe = data["total_with_exchange"]
        except Exception:
            pass
    elif raw_twe is None and existing_payment is not None:
        raw_twe = existing_payment.total_with_exchange

    raw_bc = data.get("bank_charges")
    if raw_bc is None and existing_payment is not None:
        raw_bc = existing_payment.bank_charges

    raw_sc = data.get("swift_charges")
    if raw_sc is None and existing_payment is not None:
        raw_sc = existing_payment.swift_charges

    if data.get("total_outflow") is None and any(
        v is not None for v in (raw_twe, raw_bc, raw_sc)
    ):
        try:
            base_val = Decimal(str(raw_twe)) if raw_twe is not None else amount_paid
            bc_val = Decimal(str(raw_bc)) if raw_bc is not None else Decimal("0.00")
            sc_val = Decimal(str(raw_sc)) if raw_sc is not None else Decimal("0.00")
            data["total_outflow"] = str((base_val + bc_val + sc_val).quantize(Decimal("0.01")))
        except Exception:
            pass


def _recalculate_project_payments(
    project_id: int,
    override_tsv: Decimal | None = None,
) -> None:
    payments = list_supplier_payments(project_id=project_id)
    if not payments:
        return

    tsv = _try_positive_decimal(override_tsv)
    if tsv is None:
        for p in reversed(payments):
            tsv = _try_positive_decimal(p.total_supplier_value)
            if tsv is not None:
                break
    if tsv is None:
        try:
            tsv = _resolve_total_supplier_value(project_id)
        except TotalSupplierValueRequiredError:
            return

    tsv = tsv.quantize(Decimal("0.01"))
    running_paid = Decimal("0.00")
    for p in payments:
        amt = Decimal(str(p.amount_paid or 0)).quantize(Decimal("0.01"))
        running_paid += amt
        p.total_supplier_value = tsv
        if tsv > Decimal("0.00"):
            p.payment_percentage = ((amt / tsv) * Decimal("100")).quantize(Decimal("0.01"))
            pend = (tsv - running_paid).quantize(Decimal("0.01"))
            p.pending_amount = pend if pend > Decimal("0.00") else Decimal("0.00")


def get_supplier_payment_summary(project_id: int) -> dict:
    project = get_project(project_id)
    if project is None:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found.")

    payments = list_supplier_payments(project_id=project_id)
    tsv = Decimal("0.00")
    try:
        tsv = _resolve_total_supplier_value(project_id).quantize(Decimal("0.01"))
    except TotalSupplierValueRequiredError:
        tsv = Decimal("0.00")

    total_paid = sum(
        (Decimal(str(p.amount_paid or 0)) for p in payments),
        Decimal("0.00"),
    ).quantize(Decimal("0.01"))

    if tsv > Decimal("0.00"):
        pending_amt = max((tsv - total_paid).quantize(Decimal("0.01")), Decimal("0.00"))
        paid_pct = min(
            ((total_paid / tsv) * Decimal("100")).quantize(Decimal("0.01")),
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
    return {
        "project_id": project_id,
        "supplier_id": latest.supplier_id if latest else project.supplier_id,
        "currency": latest.currency if latest else "INR",
        "total_supplier_value": f"{tsv:.2f}",
        "total_paid_amount": f"{total_paid:.2f}",
        "pending_amount": f"{pending_amt:.2f}",
        "cumulative_payment_percentage": f"{paid_pct:.2f}",
        "pending_percentage": f"{pending_pct:.2f}",
        "is_payment_completed": is_completed,
        "payment_status": payment_status,
        "payment_status_message": status_message,
        "payment_count": len(payments),
    }


def create_supplier_payment_transaction(
    *, data: dict, user_id: int | None = None
) -> SupplierPayment:
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

    _recalculate_project_payments(
        project_id,
        override_tsv=_try_positive_decimal(data.get("total_supplier_value")),
    )
    db.session.flush()

    remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
    from app.services.step_remark_service import sync_step_remarks
    sync_step_remarks(
        project_id=project_id,
        step_number=15,
        remarks_data=remarks_val,
        default_user_id=user_id,
    )

    from app.services.project_step_service import sync_supplier_payment_step
    sync_supplier_payment_step(project_id)

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
        latest_first=True,
    )


def update_supplier_payment_transaction(
    *,
    payment_id: int,
    data: dict,
    user_id: int | None = None,
) -> SupplierPayment:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        raise SupplierPaymentNotFoundError(
            f"Supplier payment with ID {payment_id} not found."
        )
    previous_project_id = payment.project_id

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

    if any(
        k in data
        for k in (
            "amount_paid",
            "total_supplier_value",
            "payment_percentage",
            "pending_amount",
            "exchange_rate",
            "total_with_exchange",
            "bank_charges",
            "swift_charges",
            "total_outflow",
        )
    ):
        _calculate_payment_amounts(data, is_update=True, existing_payment=payment)

    updated_payment = update_supplier_payment(
        payment=payment,
        data=data,
    )
    db.session.flush()

    _recalculate_project_payments(
        updated_payment.project_id,
        override_tsv=_try_positive_decimal(data.get("total_supplier_value"))
        or _try_positive_decimal(updated_payment.total_supplier_value),
    )
    if updated_payment.project_id != previous_project_id:
        _recalculate_project_payments(previous_project_id)
    db.session.flush()

    if "remarks" in data or "remark" in data:
        remarks_val = data.get("remarks") if "remarks" in data else data.get("remark")
        from app.services.step_remark_service import sync_step_remarks
        sync_step_remarks(
            project_id=updated_payment.project_id,
            step_number=15,
            remarks_data=remarks_val,
            default_user_id=user_id,
        )

    from app.services.project_step_service import sync_supplier_payment_step
    sync_supplier_payment_step(updated_payment.project_id)
    if updated_payment.project_id != previous_project_id:
        sync_supplier_payment_step(previous_project_id)

    return updated_payment


def delete_supplier_payment_transaction(payment_id: int) -> list[str]:
    payment = get_supplier_payment(payment_id)
    if payment is None:
        raise SupplierPaymentNotFoundError(
            f"Supplier payment with ID {payment_id} not found."
        )

    project_id = payment.project_id
    storage_keys = delete_supplier_payment(payment_id)
    db.session.flush()

    _recalculate_project_payments(project_id)
    db.session.flush()

    remaining = SupplierPayment.query.filter_by(project_id=project_id).first()
    if not remaining:
        from app.services.step_remark_service import sync_step_remarks
        sync_step_remarks(
            project_id=project_id,
            step_number=15,
            remarks_data=None,
        )

    from app.services.project_step_service import sync_supplier_payment_step
    sync_supplier_payment_step(project_id)

    return storage_keys
