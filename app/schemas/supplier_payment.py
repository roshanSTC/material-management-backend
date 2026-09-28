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
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValidationError(f"Invalid date format: {val}")


class SupplierPaymentCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    currency = fields.String(
        required=False,
        load_default="INR",
        validate=validate.Length(max=10),
    )
    payment_percentage = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    total_supplier_value = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    amount_paid = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    payment_date = fields.Date(required=True)
    transaction_details = fields.String(
        required=False,
        allow_none=True,
    )
    pending_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    exchange_rate = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    total_with_exchange = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    bank_charges_currency = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=10),
    )
    bank_charges = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    swift_charges = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    total_outflow = fields.Decimal(
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

    @validates_schema
    def validate_amount_or_percentage(self, data, **kwargs):
        if data.get("amount_paid") is None and data.get("payment_percentage") is None:
            raise ValidationError(
                "Either amount_paid or payment_percentage is required.",
                field_name="amount_paid",
            )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle project_id
        pid = normalized.get("project_id") if normalized.get("project_id") is not None else normalized.get("projectId")
        if pid is not None:
            try:
                normalized["project_id"] = int(pid)
            except (ValueError, TypeError):
                pass

        # Handle supplier_id
        sid = normalized.get("supplier_id") if normalized.get("supplier_id") is not None else normalized.get("supplierId")
        if sid is not None:
            try:
                normalized["supplier_id"] = int(sid)
            except (ValueError, TypeError):
                pass

        # Handle currency
        if "currency" in normalized and normalized["currency"] is not None:
            normalized["currency"] = str(normalized["currency"]).strip().upper()

        # Handle payment_percentage
        pct = (
            normalized.get("payment_percentage")
            if normalized.get("payment_percentage") is not None
            else normalized.get("paymentPercentage")
        )
        if pct is None:
            pct = normalized.get("percentage")
        if pct is not None:
            normalized["payment_percentage"] = pct

        # Handle total_supplier_value
        tsv = (
            normalized.get("total_supplier_value")
            if normalized.get("total_supplier_value") is not None
            else normalized.get("totalSupplierValue")
        )
        if tsv is None:
            tsv = normalized.get("supplier_value")
        if tsv is not None:
            normalized["total_supplier_value"] = tsv

        # Handle amount_paid
        amt = (
            normalized.get("amount_paid")
            if normalized.get("amount_paid") is not None
            else normalized.get("amountPaid")
        )
        if amt is None:
            amt = normalized.get("amount")
        if amt is not None:
            normalized["amount_paid"] = amt

        # Handle payment_date
        pay_date = (
            normalized.get("payment_date")
            if normalized.get("payment_date") is not None
            else normalized.get("paymentDate")
        )
        if pay_date is not None:
            parsed = _parse_date(pay_date)
            if parsed is not None:
                normalized["payment_date"] = parsed.isoformat()

        # Handle transaction_details
        tx = (
            normalized.get("transaction_details")
            if normalized.get("transaction_details") is not None
            else normalized.get("transactionDetails")
        )
        if tx is not None:
            normalized["transaction_details"] = tx

        # Handle pending_amount
        pend = (
            normalized.get("pending_amount")
            if normalized.get("pending_amount") is not None
            else normalized.get("pendingAmount")
        )
        if pend is not None:
            normalized["pending_amount"] = pend

        # Handle exchange_rate
        ex_rate = (
            normalized.get("exchange_rate")
            if normalized.get("exchange_rate") is not None
            else normalized.get("exchangeRate")
        )
        if ex_rate is not None:
            normalized["exchange_rate"] = ex_rate

        # Handle total_with_exchange
        twe = (
            normalized.get("total_with_exchange")
            if normalized.get("total_with_exchange") is not None
            else normalized.get("totalWithExchange")
        )
        if twe is not None:
            normalized["total_with_exchange"] = twe

        # Handle bank_charges_currency
        bcc = (
            normalized.get("bank_charges_currency")
            if normalized.get("bank_charges_currency") is not None
            else normalized.get("bankChargesCurrency")
        )
        if bcc is not None:
            normalized["bank_charges_currency"] = str(bcc).strip().upper()

        # Handle bank_charges
        bc = (
            normalized.get("bank_charges")
            if normalized.get("bank_charges") is not None
            else normalized.get("bankCharges")
        )
        if bc is not None:
            normalized["bank_charges"] = bc

        # Handle swift_charges
        sc = (
            normalized.get("swift_charges")
            if normalized.get("swift_charges") is not None
            else normalized.get("swiftCharges")
        )
        if sc is not None:
            normalized["swift_charges"] = sc

        # Handle total_outflow
        to_val = (
            normalized.get("total_outflow")
            if normalized.get("total_outflow") is not None
            else normalized.get("totalOutflow")
        )
        if to_val is not None:
            normalized["total_outflow"] = to_val

        # Handle remark / remarks
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class SupplierPaymentUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    supplier_id = fields.Integer(required=False, allow_none=True)
    currency = fields.String(
        required=False,
        validate=validate.Length(max=10),
    )
    payment_percentage = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    total_supplier_value = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    amount_paid = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
    )
    payment_date = fields.Date(required=False)
    transaction_details = fields.String(
        required=False,
        allow_none=True,
    )
    pending_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    exchange_rate = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    total_with_exchange = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    bank_charges_currency = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=10),
    )
    bank_charges = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    swift_charges = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    total_outflow = fields.Decimal(
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

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "project_id" in normalized or "projectId" in normalized:
            pid = normalized.get("project_id") if normalized.get("project_id") is not None else normalized.get("projectId")
            if pid is not None:
                try:
                    normalized["project_id"] = int(pid)
                except (ValueError, TypeError):
                    pass

        if "supplier_id" in normalized or "supplierId" in normalized:
            sid = normalized.get("supplier_id") if normalized.get("supplier_id") is not None else normalized.get("supplierId")
            if sid is not None:
                try:
                    normalized["supplier_id"] = int(sid)
                except (ValueError, TypeError):
                    pass

        if "currency" in normalized and normalized["currency"] is not None:
            normalized["currency"] = str(normalized["currency"]).strip().upper()

        if "payment_percentage" in normalized or "paymentPercentage" in normalized or "percentage" in normalized:
            pct = normalized.get("payment_percentage") or normalized.get("paymentPercentage") or normalized.get("percentage")
            if pct is not None:
                normalized["payment_percentage"] = pct

        if "total_supplier_value" in normalized or "totalSupplierValue" in normalized or "supplier_value" in normalized:
            tsv = normalized.get("total_supplier_value") or normalized.get("totalSupplierValue") or normalized.get("supplier_value")
            if tsv is not None:
                normalized["total_supplier_value"] = tsv

        if "amount_paid" in normalized or "amountPaid" in normalized or "amount" in normalized:
            amt = normalized.get("amount_paid") or normalized.get("amountPaid") or normalized.get("amount")
            if amt is not None:
                normalized["amount_paid"] = amt

        if "payment_date" in normalized or "paymentDate" in normalized:
            pay_date = normalized.get("payment_date") or normalized.get("paymentDate")
            if pay_date is not None:
                parsed = _parse_date(pay_date)
                if parsed is not None:
                    normalized["payment_date"] = parsed.isoformat()

        if "transaction_details" in normalized or "transactionDetails" in normalized:
            tx = normalized.get("transaction_details") or normalized.get("transactionDetails")
            if tx is not None:
                normalized["transaction_details"] = tx

        if "pending_amount" in normalized or "pendingAmount" in normalized:
            pend = normalized.get("pending_amount") or normalized.get("pendingAmount")
            if pend is not None:
                normalized["pending_amount"] = pend

        if "exchange_rate" in normalized or "exchangeRate" in normalized:
            ex_rate = (
                normalized.get("exchange_rate")
                if normalized.get("exchange_rate") is not None
                else normalized.get("exchangeRate")
            )
            if ex_rate is not None:
                normalized["exchange_rate"] = ex_rate

        if "total_with_exchange" in normalized or "totalWithExchange" in normalized:
            twe = (
                normalized.get("total_with_exchange")
                if normalized.get("total_with_exchange") is not None
                else normalized.get("totalWithExchange")
            )
            if twe is not None:
                normalized["total_with_exchange"] = twe

        if "bank_charges_currency" in normalized or "bankChargesCurrency" in normalized:
            bcc = (
                normalized.get("bank_charges_currency")
                if normalized.get("bank_charges_currency") is not None
                else normalized.get("bankChargesCurrency")
            )
            if bcc is not None:
                normalized["bank_charges_currency"] = str(bcc).strip().upper()

        if "bank_charges" in normalized or "bankCharges" in normalized:
            bc = (
                normalized.get("bank_charges")
                if normalized.get("bank_charges") is not None
                else normalized.get("bankCharges")
            )
            if bc is not None:
                normalized["bank_charges"] = bc

        if "swift_charges" in normalized or "swiftCharges" in normalized:
            sc = (
                normalized.get("swift_charges")
                if normalized.get("swift_charges") is not None
                else normalized.get("swiftCharges")
            )
            if sc is not None:
                normalized["swift_charges"] = sc

        if "total_outflow" in normalized or "totalOutflow" in normalized:
            to_val = (
                normalized.get("total_outflow")
                if normalized.get("total_outflow") is not None
                else normalized.get("totalOutflow")
            )
            if to_val is not None:
                normalized["total_outflow"] = to_val

        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class SupplierPaymentResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    supplier_id = fields.Integer(dump_only=True)
    currency = fields.String(dump_only=True)
    payment_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    cumulative_payment_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    pending_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_supplier_value = fields.Decimal(dump_only=True, as_string=True, places=2)
    amount_paid = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_paid_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_date = fields.Date(dump_only=True)
    transaction_details = fields.String(dump_only=True)
    pending_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    exchange_rate = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_with_exchange = fields.Decimal(dump_only=True, as_string=True, places=2)
    bank_charges_currency = fields.String(dump_only=True)
    bank_charges = fields.Decimal(dump_only=True, as_string=True, places=2)
    swift_charges = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_outflow = fields.Decimal(dump_only=True, as_string=True, places=2)
    is_payment_completed = fields.Boolean(dump_only=True)
    payment_status = fields.String(dump_only=True)
    payment_status_message = fields.String(dump_only=True)
    remarks = fields.Raw(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
    )


class SupplierPaymentQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    supplier_id = fields.Integer(required=False)
    currency = fields.String(required=False)