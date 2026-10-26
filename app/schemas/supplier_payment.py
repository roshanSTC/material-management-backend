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


def _clean_decimal_or_none(val):
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        Decimal(s)
        return s
    except Exception:
        return val


class SupplierPaymentCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True)
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
    items = fields.Raw(
        required=False,
        allow_none=True,
    )
    attachments_count = fields.Raw(
        required=False,
        allow_none=True,
    )
    form_code = fields.Raw(
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
        pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if pid is not None and str(pid).strip() != "":
            try:
                normalized["project_id"] = int(pid)
            except (ValueError, TypeError):
                pass

        # Handle supplier_id
        sid = (
            normalized.get("supplier_id")
            if normalized.get("supplier_id") is not None
            else normalized.get("supplierId")
        )
        if sid is not None and str(sid).strip() != "":
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
        if pct is None:
            pct = normalized.get("payment_pct")
        if pct is None:
            pct = normalized.get("paymentPct")
        clean_pct = _clean_decimal_or_none(pct)
        if clean_pct is not None:
            normalized["payment_percentage"] = clean_pct

        # Handle total_supplier_value
        tsv = (
            normalized.get("total_supplier_value")
            if normalized.get("total_supplier_value") is not None
            else normalized.get("totalSupplierValue")
        )
        if tsv is None:
            tsv = normalized.get("supplier_value")
        if tsv is None:
            tsv = normalized.get("total_contract_value")
        if tsv is None:
            tsv = normalized.get("totalContractValue")
        if tsv is None:
            tsv = normalized.get("contract_value")
        clean_tsv = _clean_decimal_or_none(tsv)
        if clean_tsv is not None:
            normalized["total_supplier_value"] = clean_tsv

        # Handle amount_paid
        amt = (
            normalized.get("amount_paid")
            if normalized.get("amount_paid") is not None
            else normalized.get("amountPaid")
        )
        if amt is None:
            amt = normalized.get("amount")
        if amt is None:
            amt = normalized.get("payment_amount")
        if amt is None:
            amt = normalized.get("paymentAmount")
        clean_amt = _clean_decimal_or_none(amt)
        if clean_amt is not None:
            normalized["amount_paid"] = clean_amt

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
        if tx is None:
            tx = normalized.get("reference_no")
        if tx is None:
            tx = normalized.get("referenceNo")
        if tx is None:
            tx = normalized.get("reference_number")
        if tx is None:
            tx = normalized.get("ref_no")
        if tx is not None and str(tx).strip() != "":
            normalized["transaction_details"] = str(tx).strip()

        # Handle pending_amount
        pend = (
            normalized.get("pending_amount")
            if normalized.get("pending_amount") is not None
            else normalized.get("pendingAmount")
        )
        clean_pend = _clean_decimal_or_none(pend)
        if clean_pend is not None:
            normalized["pending_amount"] = clean_pend

        # Handle exchange_rate
        ex_rate = (
            normalized.get("exchange_rate")
            if normalized.get("exchange_rate") is not None
            else normalized.get("exchangeRate")
        )
        if ex_rate is None:
            ex_rate = normalized.get("eur_to_inr_rate")
        if ex_rate is None:
            ex_rate = normalized.get("eurToInrRate")
        clean_ex = _clean_decimal_or_none(ex_rate)
        if clean_ex is not None:
            normalized["exchange_rate"] = clean_ex

        # Handle total_with_exchange
        twe = (
            normalized.get("total_with_exchange")
            if normalized.get("total_with_exchange") is not None
            else normalized.get("totalWithExchange")
        )
        if twe is None:
            twe = normalized.get("payment_amount_inr")
        if twe is None:
            twe = normalized.get("paymentAmountInr")
        clean_twe = _clean_decimal_or_none(twe)
        if clean_twe is not None:
            normalized["total_with_exchange"] = clean_twe

        # Handle bank_charges_currency
        bcc = (
            normalized.get("bank_charges_currency")
            if normalized.get("bank_charges_currency") is not None
            else normalized.get("bankChargesCurrency")
        )
        if bcc is not None and str(bcc).strip() != "":
            normalized["bank_charges_currency"] = str(bcc).strip().upper()

        # Handle bank_charges
        bc = (
            normalized.get("bank_charges")
            if normalized.get("bank_charges") is not None
            else normalized.get("bankCharges")
        )
        clean_bc = _clean_decimal_or_none(bc)
        if clean_bc is not None:
            normalized["bank_charges"] = clean_bc

        # Handle swift_charges
        sc = (
            normalized.get("swift_charges")
            if normalized.get("swift_charges") is not None
            else normalized.get("swiftCharges")
        )
        clean_sc = _clean_decimal_or_none(sc)
        if clean_sc is not None:
            normalized["swift_charges"] = clean_sc

        # Handle total_outflow
        to_val = (
            normalized.get("total_outflow")
            if normalized.get("total_outflow") is not None
            else normalized.get("totalOutflow")
        )
        clean_to = _clean_decimal_or_none(to_val)
        if clean_to is not None:
            normalized["total_outflow"] = clean_to

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
    supplier_name = fields.String(required=False, allow_none=True)
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
        allow_none=True,
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
    items = fields.Raw(
        required=False,
        allow_none=True,
    )
    attachments_count = fields.Raw(
        required=False,
        allow_none=True,
    )
    form_code = fields.Raw(
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "project_id" in normalized or "projectId" in normalized:
            pid = (
                normalized.get("project_id")
                if normalized.get("project_id") is not None
                else normalized.get("projectId")
            )
            if pid is not None and str(pid).strip() != "":
                try:
                    normalized["project_id"] = int(pid)
                except (ValueError, TypeError):
                    pass

        if "supplier_id" in normalized or "supplierId" in normalized:
            sid = (
                normalized.get("supplier_id")
                if normalized.get("supplier_id") is not None
                else normalized.get("supplierId")
            )
            if sid is not None and str(sid).strip() != "":
                try:
                    normalized["supplier_id"] = int(sid)
                except (ValueError, TypeError):
                    pass

        if "currency" in normalized and normalized["currency"] is not None:
            normalized["currency"] = str(normalized["currency"]).strip().upper()

        if any(k in normalized for k in ("payment_percentage", "paymentPercentage", "percentage", "payment_pct", "paymentPct")):
            pct = (
                normalized.get("payment_percentage")
                if normalized.get("payment_percentage") is not None
                else normalized.get("paymentPercentage")
            )
            if pct is None:
                pct = normalized.get("percentage")
            if pct is None:
                pct = normalized.get("payment_pct")
            if pct is None:
                pct = normalized.get("paymentPct")
            clean_pct = _clean_decimal_or_none(pct)
            if clean_pct is not None:
                normalized["payment_percentage"] = clean_pct

        if any(k in normalized for k in ("total_supplier_value", "totalSupplierValue", "supplier_value", "total_contract_value", "totalContractValue", "contract_value")):
            tsv = (
                normalized.get("total_supplier_value")
                if normalized.get("total_supplier_value") is not None
                else normalized.get("totalSupplierValue")
            )
            if tsv is None:
                tsv = normalized.get("supplier_value")
            if tsv is None:
                tsv = normalized.get("total_contract_value")
            if tsv is None:
                tsv = normalized.get("totalContractValue")
            if tsv is None:
                tsv = normalized.get("contract_value")
            clean_tsv = _clean_decimal_or_none(tsv)
            if clean_tsv is not None:
                normalized["total_supplier_value"] = clean_tsv

        if any(k in normalized for k in ("amount_paid", "amountPaid", "amount", "payment_amount", "paymentAmount")):
            amt = (
                normalized.get("amount_paid")
                if normalized.get("amount_paid") is not None
                else normalized.get("amountPaid")
            )
            if amt is None:
                amt = normalized.get("amount")
            if amt is None:
                amt = normalized.get("payment_amount")
            if amt is None:
                amt = normalized.get("paymentAmount")
            clean_amt = _clean_decimal_or_none(amt)
            if clean_amt is not None:
                normalized["amount_paid"] = clean_amt

        if "payment_date" in normalized or "paymentDate" in normalized:
            pay_date = normalized.get("payment_date") or normalized.get("paymentDate")
            if pay_date is not None:
                parsed = _parse_date(pay_date)
                if parsed is not None:
                    normalized["payment_date"] = parsed.isoformat()

        if any(k in normalized for k in ("transaction_details", "transactionDetails", "reference_no", "referenceNo", "reference_number", "ref_no")):
            tx = (
                normalized.get("transaction_details")
                if normalized.get("transaction_details") is not None
                else normalized.get("transactionDetails")
            )
            if tx is None:
                tx = normalized.get("reference_no")
            if tx is None:
                tx = normalized.get("referenceNo")
            if tx is None:
                tx = normalized.get("reference_number")
            if tx is None:
                tx = normalized.get("ref_no")
            if tx is not None and str(tx).strip() != "":
                normalized["transaction_details"] = str(tx).strip()

        if "pending_amount" in normalized or "pendingAmount" in normalized:
            pend = normalized.get("pending_amount") or normalized.get("pendingAmount")
            clean_pend = _clean_decimal_or_none(pend)
            if clean_pend is not None:
                normalized["pending_amount"] = clean_pend

        if any(k in normalized for k in ("exchange_rate", "exchangeRate", "eur_to_inr_rate", "eurToInrRate")):
            ex_rate = (
                normalized.get("exchange_rate")
                if normalized.get("exchange_rate") is not None
                else normalized.get("exchangeRate")
            )
            if ex_rate is None:
                ex_rate = normalized.get("eur_to_inr_rate")
            if ex_rate is None:
                ex_rate = normalized.get("eurToInrRate")
            clean_ex = _clean_decimal_or_none(ex_rate)
            if clean_ex is not None:
                normalized["exchange_rate"] = clean_ex

        if any(k in normalized for k in ("total_with_exchange", "totalWithExchange", "payment_amount_inr", "paymentAmountInr")):
            twe = (
                normalized.get("total_with_exchange")
                if normalized.get("total_with_exchange") is not None
                else normalized.get("totalWithExchange")
            )
            if twe is None:
                twe = normalized.get("payment_amount_inr")
            if twe is None:
                twe = normalized.get("paymentAmountInr")
            clean_twe = _clean_decimal_or_none(twe)
            if clean_twe is not None:
                normalized["total_with_exchange"] = clean_twe

        if "bank_charges_currency" in normalized or "bankChargesCurrency" in normalized:
            bcc = (
                normalized.get("bank_charges_currency")
                if normalized.get("bank_charges_currency") is not None
                else normalized.get("bankChargesCurrency")
            )
            if bcc is not None and str(bcc).strip() != "":
                normalized["bank_charges_currency"] = str(bcc).strip().upper()

        if "bank_charges" in normalized or "bankCharges" in normalized:
            bc = (
                normalized.get("bank_charges")
                if normalized.get("bank_charges") is not None
                else normalized.get("bankCharges")
            )
            clean_bc = _clean_decimal_or_none(bc)
            if clean_bc is not None:
                normalized["bank_charges"] = clean_bc

        if "swift_charges" in normalized or "swiftCharges" in normalized:
            sc = (
                normalized.get("swift_charges")
                if normalized.get("swift_charges") is not None
                else normalized.get("swiftCharges")
            )
            clean_sc = _clean_decimal_or_none(sc)
            if clean_sc is not None:
                normalized["swift_charges"] = clean_sc

        if "total_outflow" in normalized or "totalOutflow" in normalized:
            to_val = (
                normalized.get("total_outflow")
                if normalized.get("total_outflow") is not None
                else normalized.get("totalOutflow")
            )
            clean_to = _clean_decimal_or_none(to_val)
            if clean_to is not None:
                normalized["total_outflow"] = clean_to

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
    payment_pct = fields.Decimal(dump_only=True, as_string=True, places=2, attribute="payment_percentage")
    cumulative_payment_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    pending_percentage = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_supplier_value = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_contract_value = fields.Decimal(dump_only=True, as_string=True, places=2, attribute="total_supplier_value")
    amount_paid = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_amount = fields.Decimal(dump_only=True, as_string=True, places=2, attribute="amount_paid")
    total_paid_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    remaining_amount_before_transaction = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_date = fields.Date(dump_only=True)
    transaction_details = fields.String(dump_only=True)
    reference_no = fields.String(dump_only=True, attribute="transaction_details")
    pending_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    exchange_rate = fields.Decimal(dump_only=True, as_string=True, places=2)
    eur_to_inr_rate = fields.Decimal(dump_only=True, as_string=True, places=2, attribute="exchange_rate")
    total_with_exchange = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_amount_inr = fields.Decimal(dump_only=True, as_string=True, places=2, attribute="total_with_exchange")
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
