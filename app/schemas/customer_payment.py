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
        raise ValidationError(f"Invalid date format: {val}")


class CustomerPaymentCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    invoice_no = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    invoice_date = fields.Date(required=True)
    invoice_value = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
    )
    payment_amount = fields.Decimal(
        required=True,
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
    remark = fields.String(
        required=False,
        allow_none=True,
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

        # Handle invoice_no
        inv_no = (
            normalized.get("invoice_no")
            if normalized.get("invoice_no") is not None
            else normalized.get("invoiceNo")
        )
        if inv_no is None:
            inv_no = (
                normalized.get("invoice_number")
                if normalized.get("invoice_number") is not None
                else normalized.get("invoiceNumber")
            )
        if inv_no is not None:
            normalized["invoice_no"] = str(inv_no).strip()

        # Handle invoice_date
        inv_date = (
            normalized.get("invoice_date")
            if normalized.get("invoice_date") is not None
            else normalized.get("invoiceDate")
        )
        if inv_date is not None:
            parsed = _parse_date(inv_date)
            if parsed is not None:
                normalized["invoice_date"] = parsed.isoformat()

        # Handle invoice_value
        inv_val = (
            normalized.get("invoice_value")
            if normalized.get("invoice_value") is not None
            else normalized.get("invoiceValue")
        )
        if inv_val is not None:
            normalized["invoice_value"] = inv_val

        # Handle payment_amount
        pay_amt = (
            normalized.get("payment_amount")
            if normalized.get("payment_amount") is not None
            else normalized.get("paymentAmount")
        )
        if pay_amt is None:
            pay_amt = normalized.get("amount")
        if pay_amt is not None:
            normalized["payment_amount"] = pay_amt

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

        # Handle ld
        ld_val = normalized.get("ld")
        if ld_val is None:
            ld_val = (
                normalized.get("liquidated_damages")
                if normalized.get("liquidated_damages") is not None
                else normalized.get("liquidatedDamages")
            )
        if ld_val is not None:
            normalized["ld"] = ld_val

        # Handle remark
        rem = (
            normalized.get("remark")
            if normalized.get("remark") is not None
            else normalized.get("remarks")
        )
        if rem is not None:
            normalized["remark"] = rem

        return normalized


class CustomerPaymentUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    invoice_no = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    invoice_date = fields.Date(required=False)
    invoice_value = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
    )
    payment_amount = fields.Decimal(
        required=False,
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
    remark = fields.String(
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

        if "invoice_no" in normalized or "invoiceNo" in normalized or "invoice_number" in normalized or "invoiceNumber" in normalized:
            inv_no = normalized.get("invoice_no") or normalized.get("invoiceNo") or normalized.get("invoice_number") or normalized.get("invoiceNumber")
            if inv_no is not None:
                normalized["invoice_no"] = str(inv_no).strip()

        if "invoice_date" in normalized or "invoiceDate" in normalized:
            inv_date = normalized.get("invoice_date") or normalized.get("invoiceDate")
            if inv_date is not None:
                parsed = _parse_date(inv_date)
                if parsed is not None:
                    normalized["invoice_date"] = parsed.isoformat()

        if "invoice_value" in normalized or "invoiceValue" in normalized:
            inv_val = normalized.get("invoice_value") or normalized.get("invoiceValue")
            if inv_val is not None:
                normalized["invoice_value"] = inv_val

        if "payment_amount" in normalized or "paymentAmount" in normalized or "amount" in normalized:
            pay_amt = normalized.get("payment_amount") or normalized.get("paymentAmount") or normalized.get("amount")
            if pay_amt is not None:
                normalized["payment_amount"] = pay_amt

        if "payment_date" in normalized or "paymentDate" in normalized:
            pay_date = normalized.get("payment_date") or normalized.get("paymentDate")
            if pay_date is not None:
                parsed = _parse_date(pay_date)
                if parsed is not None:
                    normalized["payment_date"] = parsed.isoformat()

        if "ld" in normalized or "liquidated_damages" in normalized or "liquidatedDamages" in normalized:
            ld_val = normalized.get("ld")
            if ld_val is None:
                ld_val = normalized.get("liquidated_damages") or normalized.get("liquidatedDamages")
            if ld_val is not None:
                normalized["ld"] = ld_val

        if "remark" in normalized or "remarks" in normalized:
            rem = normalized.get("remark") or normalized.get("remarks")
            if rem is not None:
                normalized["remark"] = rem

        return normalized


class CustomerPaymentResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    invoice_no = fields.String(dump_only=True)
    invoice_number = fields.String(dump_only=True)
    invoice_date = fields.Date(dump_only=True)
    invoice_value = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    payment_date = fields.Date(dump_only=True)
    tds = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    ld = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    liquidated_damages = fields.Decimal(dump_only=True, as_string=True, places=2, allow_none=True)
    remark = fields.String(dump_only=True)
    remarks = fields.String(dump_only=True)
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
