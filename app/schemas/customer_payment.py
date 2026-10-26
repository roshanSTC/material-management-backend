from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates_schema,
)

from app.schemas.attachment import AttachmentResponseSchema


def _not_blank(value: str) -> None:
    if not value or not str(value).strip():
        raise ValidationError("Field must not be blank.")


def _parse_date(val):
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s)
    except Exception:
        raise ValidationError(f"Invalid date format: {val}")


class CustomerPaymentCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    invoice_date = fields.Date(required=False, allow_none=True)
    payment_percentage = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    invoice_value = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    payment_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    pending_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    payment_date = fields.Date(required=True)
    tds = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    ld = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    remark = fields.Raw(
        required=False,
        allow_none=True,
    )
    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Raw(),
        required=False,
        allow_none=True,
    )
    attachments_count = fields.Integer(
        required=False,
        allow_none=True,
    )
    form_code = fields.String(
        required=False,
        allow_none=True,
    )

    @validates_schema
    def validate_amount_or_percentage(self, data, **kwargs):
        if data.get("payment_amount") is None and data.get("payment_percentage") is None:
            raise ValidationError(
                "Either payment_amount or payment_percentage is required.",
                field_name="payment_amount",
            )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle project_id
        pid = normalized.get("project_id") if normalized.get("project_id") is not None else normalized.get("projectId")
        if pid is not None and str(pid).strip() != "":
            try:
                normalized["project_id"] = int(pid)
            except (ValueError, TypeError):
                pass
        elif pid == "":
            normalized.pop("project_id", None)

        # Handle invoice_no
        inv_no = (
            normalized.get("invoice_no")
            if normalized.get("invoice_no") is not None
            else (
                normalized.get("invoiceNo")
                if normalized.get("invoiceNo") is not None
                else (
                    normalized.get("invoice_number")
                    if normalized.get("invoice_number") is not None
                    else (
                        normalized.get("invoiceNumber")
                        if normalized.get("invoiceNumber") is not None
                        else (
                            normalized.get("payment_against_invoice_no")
                            if normalized.get("payment_against_invoice_no") is not None
                            else (
                                normalized.get("paymentAgainstInvoiceNo")
                                if normalized.get("paymentAgainstInvoiceNo") is not None
                                else (
                                    normalized.get("against_invoice_no")
                                    if normalized.get("against_invoice_no") is not None
                                    else normalized.get("againstInvoiceNo")
                                )
                            )
                        )
                    )
                )
            )
        )
        if inv_no is not None:
            s_inv = str(inv_no).strip()
            normalized["invoice_no"] = s_inv if s_inv else None

        # Handle invoice_date
        inv_date = (
            normalized.get("invoice_date")
            if normalized.get("invoice_date") is not None
            else normalized.get("invoiceDate")
        )
        if inv_date is not None and str(inv_date).strip() != "":
            parsed = _parse_date(inv_date)
            if parsed is not None:
                normalized["invoice_date"] = parsed.isoformat()
        elif inv_date == "":
            normalized["invoice_date"] = None

        # Handle payment_percentage
        pct = (
            normalized.get("payment_percentage")
            if normalized.get("payment_percentage") is not None
            else (
                normalized.get("paymentPercentage")
                if normalized.get("paymentPercentage") is not None
                else (
                    normalized.get("percentage")
                    if normalized.get("percentage") is not None
                    else (
                        normalized.get("payment_pct")
                        if normalized.get("payment_pct") is not None
                        else normalized.get("paymentPct")
                    )
                )
            )
        )
        if pct is not None and str(pct).strip() != "":
            normalized["payment_percentage"] = pct
        elif pct == "":
            normalized["payment_percentage"] = None

        # Handle invoice_value
        inv_val = (
            normalized.get("invoice_value")
            if normalized.get("invoice_value") is not None
            else (
                normalized.get("invoiceValue")
                if normalized.get("invoiceValue") is not None
                else (
                    normalized.get("total_customer_value")
                    if normalized.get("total_customer_value") is not None
                    else (
                        normalized.get("totalCustomerValue")
                        if normalized.get("totalCustomerValue") is not None
                        else (
                            normalized.get("total_invoice_value")
                            if normalized.get("total_invoice_value") is not None
                            else normalized.get("totalInvoiceValue")
                        )
                    )
                )
            )
        )
        if inv_val is not None and str(inv_val).strip() != "":
            normalized["invoice_value"] = inv_val
        elif inv_val == "":
            normalized["invoice_value"] = None

        # Handle payment_amount
        pay_amt = (
            normalized.get("payment_amount")
            if normalized.get("payment_amount") is not None
            else (
                normalized.get("paymentAmount")
                if normalized.get("paymentAmount") is not None
                else (
                    normalized.get("payment_received")
                    if normalized.get("payment_received") is not None
                    else (
                        normalized.get("paymentReceived")
                        if normalized.get("paymentReceived") is not None
                        else (
                            normalized.get("amount")
                            if normalized.get("amount") is not None
                            else (
                                normalized.get("amount_paid")
                                if normalized.get("amount_paid") is not None
                                else (
                                    normalized.get("amountPaid")
                                    if normalized.get("amountPaid") is not None
                                    else (
                                        normalized.get("amount_received")
                                        if normalized.get("amount_received") is not None
                                        else normalized.get("amountReceived")
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        if pay_amt is not None and str(pay_amt).strip() != "":
            normalized["payment_amount"] = pay_amt
        elif pay_amt == "":
            normalized["payment_amount"] = None

        # Handle pending_amount
        pend = (
            normalized.get("pending_amount")
            if normalized.get("pending_amount") is not None
            else (
                normalized.get("pendingAmount")
                if normalized.get("pendingAmount") is not None
                else (
                    normalized.get("balance_amount")
                    if normalized.get("balance_amount") is not None
                    else (
                        normalized.get("balanceAmount")
                        if normalized.get("balanceAmount") is not None
                        else (
                            normalized.get("balance")
                            if normalized.get("balance") is not None
                            else (
                                normalized.get("outstanding_amount")
                                if normalized.get("outstanding_amount") is not None
                                else normalized.get("outstandingAmount")
                            )
                        )
                    )
                )
            )
        )
        if pend is not None and str(pend).strip() != "":
            normalized["pending_amount"] = pend
        elif pend == "":
            normalized["pending_amount"] = None

        # Handle payment_date
        pay_date = (
            normalized.get("payment_date")
            if normalized.get("payment_date") is not None
            else (
                normalized.get("paymentDate")
                if normalized.get("paymentDate") is not None
                else (
                    normalized.get("payment_received_date")
                    if normalized.get("payment_received_date") is not None
                    else normalized.get("paymentReceivedDate")
                )
            )
        )
        if pay_date is not None and str(pay_date).strip() != "":
            parsed = _parse_date(pay_date)
            if parsed is not None:
                normalized["payment_date"] = parsed.isoformat()
        elif pay_date == "":
            normalized["payment_date"] = None

        # Handle tds
        tds_val = (
            normalized.get("tds")
            if normalized.get("tds") is not None
            else (
                normalized.get("tds_deducted")
                if normalized.get("tds_deducted") is not None
                else (
                    normalized.get("tdsDeducted")
                    if normalized.get("tdsDeducted") is not None
                    else (
                        normalized.get("tds_amount")
                        if normalized.get("tds_amount") is not None
                        else normalized.get("tdsAmount")
                    )
                )
            )
        )
        if tds_val is not None and str(tds_val).strip() != "":
            normalized["tds"] = tds_val
        elif tds_val == "":
            normalized["tds"] = None

        # Handle ld
        ld_val = (
            normalized.get("ld")
            if normalized.get("ld") is not None
            else (
                normalized.get("ld_deducted")
                if normalized.get("ld_deducted") is not None
                else (
                    normalized.get("ldDeducted")
                    if normalized.get("ldDeducted") is not None
                    else (
                        normalized.get("liquidated_damages")
                        if normalized.get("liquidated_damages") is not None
                        else (
                            normalized.get("liquidatedDamages")
                            if normalized.get("liquidatedDamages") is not None
                            else (
                                normalized.get("ld_amount")
                                if normalized.get("ld_amount") is not None
                                else normalized.get("ldAmount")
                            )
                        )
                    )
                )
            )
        )
        if ld_val is not None and str(ld_val).strip() != "":
            normalized["ld"] = ld_val
        elif ld_val == "":
            normalized["ld"] = None

        # Handle remark / remarks
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class CustomerPaymentUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    invoice_date = fields.Date(required=False, allow_none=True)
    payment_percentage = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    invoice_value = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    payment_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    pending_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    payment_date = fields.Date(required=False)
    tds = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    ld = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    remark = fields.Raw(
        required=False,
        allow_none=True,
    )
    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Raw(),
        required=False,
        allow_none=True,
    )
    attachments_count = fields.Integer(
        required=False,
        allow_none=True,
    )
    form_code = fields.String(
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "project_id" in normalized or "projectId" in normalized:
            pid = normalized.get("project_id") if normalized.get("project_id") is not None else normalized.get("projectId")
            if pid is not None and str(pid).strip() != "":
                try:
                    normalized["project_id"] = int(pid)
                except (ValueError, TypeError):
                    pass
            elif pid == "":
                normalized["project_id"] = None

        inv_no = (
            normalized.get("invoice_no")
            if normalized.get("invoice_no") is not None
            else (
                normalized.get("invoiceNo")
                if normalized.get("invoiceNo") is not None
                else (
                    normalized.get("invoice_number")
                    if normalized.get("invoice_number") is not None
                    else (
                        normalized.get("invoiceNumber")
                        if normalized.get("invoiceNumber") is not None
                        else (
                            normalized.get("payment_against_invoice_no")
                            if normalized.get("payment_against_invoice_no") is not None
                            else (
                                normalized.get("paymentAgainstInvoiceNo")
                                if normalized.get("paymentAgainstInvoiceNo") is not None
                                else (
                                    normalized.get("against_invoice_no")
                                    if normalized.get("against_invoice_no") is not None
                                    else normalized.get("againstInvoiceNo")
                                )
                            )
                        )
                    )
                )
            )
        )
        if inv_no is not None:
            s_inv = str(inv_no).strip()
            normalized["invoice_no"] = s_inv if s_inv else None

        if "invoice_date" in normalized or "invoiceDate" in normalized:
            inv_date = normalized.get("invoice_date") or normalized.get("invoiceDate")
            if inv_date is not None and str(inv_date).strip() != "":
                parsed = _parse_date(inv_date)
                if parsed is not None:
                    normalized["invoice_date"] = parsed.isoformat()
            elif inv_date == "":
                normalized["invoice_date"] = None

        pct = (
            normalized.get("payment_percentage")
            if normalized.get("payment_percentage") is not None
            else (
                normalized.get("paymentPercentage")
                if normalized.get("paymentPercentage") is not None
                else (
                    normalized.get("percentage")
                    if normalized.get("percentage") is not None
                    else (
                        normalized.get("payment_pct")
                        if normalized.get("payment_pct") is not None
                        else normalized.get("paymentPct")
                    )
                )
            )
        )
        if pct is not None and str(pct).strip() != "":
            normalized["payment_percentage"] = pct
        elif pct == "":
            normalized["payment_percentage"] = None

        inv_val = (
            normalized.get("invoice_value")
            if normalized.get("invoice_value") is not None
            else (
                normalized.get("invoiceValue")
                if normalized.get("invoiceValue") is not None
                else (
                    normalized.get("total_customer_value")
                    if normalized.get("total_customer_value") is not None
                    else (
                        normalized.get("totalCustomerValue")
                        if normalized.get("totalCustomerValue") is not None
                        else (
                            normalized.get("total_invoice_value")
                            if normalized.get("total_invoice_value") is not None
                            else normalized.get("totalInvoiceValue")
                        )
                    )
                )
            )
        )
        if inv_val is not None and str(inv_val).strip() != "":
            normalized["invoice_value"] = inv_val
        elif inv_val == "":
            normalized["invoice_value"] = None

        pay_amt = (
            normalized.get("payment_amount")
            if normalized.get("payment_amount") is not None
            else (
                normalized.get("paymentAmount")
                if normalized.get("paymentAmount") is not None
                else (
                    normalized.get("payment_received")
                    if normalized.get("payment_received") is not None
                    else (
                        normalized.get("paymentReceived")
                        if normalized.get("paymentReceived") is not None
                        else (
                            normalized.get("amount")
                            if normalized.get("amount") is not None
                            else (
                                normalized.get("amount_paid")
                                if normalized.get("amount_paid") is not None
                                else (
                                    normalized.get("amountPaid")
                                    if normalized.get("amountPaid") is not None
                                    else (
                                        normalized.get("amount_received")
                                        if normalized.get("amount_received") is not None
                                        else normalized.get("amountReceived")
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
        if pay_amt is not None and str(pay_amt).strip() != "":
            normalized["payment_amount"] = pay_amt
        elif pay_amt == "":
            normalized["payment_amount"] = None

        pend = (
            normalized.get("pending_amount")
            if normalized.get("pending_amount") is not None
            else (
                normalized.get("pendingAmount")
                if normalized.get("pendingAmount") is not None
                else (
                    normalized.get("balance_amount")
                    if normalized.get("balance_amount") is not None
                    else (
                        normalized.get("balanceAmount")
                        if normalized.get("balanceAmount") is not None
                        else (
                            normalized.get("balance")
                            if normalized.get("balance") is not None
                            else (
                                normalized.get("outstanding_amount")
                                if normalized.get("outstanding_amount") is not None
                                else normalized.get("outstandingAmount")
                            )
                        )
                    )
                )
            )
        )
        if pend is not None and str(pend).strip() != "":
            normalized["pending_amount"] = pend
        elif pend == "":
            normalized["pending_amount"] = None

        pay_date = (
            normalized.get("payment_date")
            if normalized.get("payment_date") is not None
            else (
                normalized.get("paymentDate")
                if normalized.get("paymentDate") is not None
                else (
                    normalized.get("payment_received_date")
                    if normalized.get("payment_received_date") is not None
                    else normalized.get("paymentReceivedDate")
                )
            )
        )
        if pay_date is not None and str(pay_date).strip() != "":
            parsed = _parse_date(pay_date)
            if parsed is not None:
                normalized["payment_date"] = parsed.isoformat()
        elif pay_date == "":
            normalized["payment_date"] = None

        tds_val = (
            normalized.get("tds")
            if normalized.get("tds") is not None
            else (
                normalized.get("tds_deducted")
                if normalized.get("tds_deducted") is not None
                else (
                    normalized.get("tdsDeducted")
                    if normalized.get("tdsDeducted") is not None
                    else (
                        normalized.get("tds_amount")
                        if normalized.get("tds_amount") is not None
                        else normalized.get("tdsAmount")
                    )
                )
            )
        )
        if tds_val is not None and str(tds_val).strip() != "":
            normalized["tds"] = tds_val
        elif tds_val == "":
            normalized["tds"] = None

        ld_val = (
            normalized.get("ld")
            if normalized.get("ld") is not None
            else (
                normalized.get("ld_deducted")
                if normalized.get("ld_deducted") is not None
                else (
                    normalized.get("ldDeducted")
                    if normalized.get("ldDeducted") is not None
                    else (
                        normalized.get("liquidated_damages")
                        if normalized.get("liquidated_damages") is not None
                        else (
                            normalized.get("liquidatedDamages")
                            if normalized.get("liquidatedDamages") is not None
                            else (
                                normalized.get("ld_amount")
                                if normalized.get("ld_amount") is not None
                                else normalized.get("ldAmount")
                            )
                        )
                    )
                )
            )
        )
        if ld_val is not None and str(ld_val).strip() != "":
            normalized["ld"] = ld_val
        elif ld_val == "":
            normalized["ld"] = None

        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class CustomerPaymentResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    customer_id = fields.Integer(dump_only=True, allow_none=True)
    invoice_no = fields.String(dump_only=True)
    invoice_number = fields.String(dump_only=True)
    payment_against_invoice_no = fields.String(dump_only=True)
    invoice_date = fields.Date(dump_only=True)
    payment_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    cumulative_payment_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    pending_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    invoice_value = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_received = fields.Decimal(dump_only=True, as_string=True, places=2)
    amount_paid = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_paid_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    remaining_amount_before_transaction = fields.Decimal(dump_only=True, as_string=True, places=2)
    pending_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    balance_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_date = fields.Date(dump_only=True)
    payment_received_date = fields.Date(dump_only=True)
    tds = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    tds_deducted = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    ld = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    ld_deducted = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    liquidated_damages = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    is_payment_completed = fields.Boolean(dump_only=True)
    payment_status = fields.String(dump_only=True)
    payment_status_message = fields.String(dump_only=True)
    remark = fields.Raw(dump_only=True)
    remarks = fields.Raw(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
    )


class CustomerPaymentQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    invoice_no = fields.String(required=False)
