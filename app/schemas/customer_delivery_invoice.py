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


class CustomerDeliveryInvoiceItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    material_name = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
    )
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )

    @pre_load
    def normalize_item_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle material_name / material_description fallback
        mat_name = (
            normalized.get("material_name")
            if normalized.get("material_name") is not None
            else normalized.get("materialName")
        )
        if mat_name is None:
            mat_name = (
                normalized.get("material_description")
                if normalized.get("material_description") is not None
                else normalized.get("description")
            )
        if mat_name is not None:
            normalized["material_name"] = str(mat_name).strip()

        # Handle hsn_code / hsn_sac fallback
        hsn = (
            normalized.get("hsn_code")
            if normalized.get("hsn_code") is not None
            else normalized.get("hsnCode")
        )
        if hsn is None:
            hsn = (
                normalized.get("hsn_sac")
                if normalized.get("hsn_sac") is not None
                else normalized.get("hsn")
            )
        if hsn is not None:
            normalized["hsn_code"] = str(hsn).strip()

        # Handle unit_price / rate_per_unit fallback
        unit_price = (
            normalized.get("unit_price")
            if normalized.get("unit_price") is not None
            else normalized.get("unitPrice")
        )
        if unit_price is None:
            unit_price = (
                normalized.get("rate_per_unit")
                if normalized.get("rate_per_unit") is not None
                else normalized.get("rate")
            )
        if unit_price is not None:
            normalized["unit_price"] = unit_price

        # Handle net_amount / amount fallback
        net_amt = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netAmount")
        )
        if net_amt is None:
            net_amt = (
                normalized.get("amount")
                if normalized.get("amount") is not None
                else normalized.get("total_price")
            )
        if net_amt is not None:
            normalized["net_amount"] = net_amt

        return normalized


class CustomerDeliveryInvoiceItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    material_name = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
    )
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    quantity = fields.Decimal(
        required=False,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(
        required=False,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )


class CustomerDeliveryInvoiceItemResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    invoice_id = fields.Integer(dump_only=True)
    material_name = fields.String(dump_only=True)
    hsn_code = fields.String(dump_only=True)
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3)
    unit_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    net_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CustomerDeliveryInvoiceCreateSchema(Schema):
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
    gst_rate = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    gst_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    round_off = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    net_total = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(CustomerDeliveryInvoiceItemCreateSchema),
        required=False,
        load_default=list,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle invoice_no / invoice_number
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

        # Handle project_id
        pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if pid is not None:
            try:
                normalized["project_id"] = int(pid)
            except (ValueError, TypeError):
                pass

        # Handle gst_rate
        gst_r = (
            normalized.get("gst_rate")
            if normalized.get("gst_rate") is not None
            else normalized.get("gstRate")
        )
        if gst_r is None:
            gst_r = normalized.get("gst")
        if gst_r is not None:
            normalized["gst_rate"] = gst_r

        # Handle gst_amount
        gst_a = (
            normalized.get("gst_amount")
            if normalized.get("gst_amount") is not None
            else normalized.get("gstAmount")
        )
        if gst_a is not None:
            normalized["gst_amount"] = gst_a

        # Handle round_off
        ro = (
            normalized.get("round_off")
            if normalized.get("round_off") is not None
            else normalized.get("roundOff")
        )
        if ro is not None:
            normalized["round_off"] = ro

        # Handle net_total
        nt = (
            normalized.get("net_total")
            if normalized.get("net_total") is not None
            else normalized.get("netTotal")
        )
        if nt is None:
            nt = (
                normalized.get("total_amount")
                if normalized.get("total_amount") is not None
                else normalized.get("total_net_amount")
            )
        if nt is not None:
            normalized["net_total"] = nt

        # Handle remark / remarks
        rem = (
            normalized.get("remark")
            if normalized.get("remark") is not None
            else normalized.get("remarks")
        )
        if rem is not None:
            normalized["remark"] = rem

        return normalized


class CustomerDeliveryInvoiceUpdateSchema(Schema):
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
    gst_rate = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    gst_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    round_off = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    net_total = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(CustomerDeliveryInvoiceItemCreateSchema),
        required=False,
    )

    @pre_load
    def normalize_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "invoice_no" in normalized or "invoice_number" in normalized or "invoiceNo" in normalized:
            inv_no = normalized.get("invoice_no") or normalized.get("invoice_number") or normalized.get("invoiceNo")
            if inv_no is not None:
                normalized["invoice_no"] = str(inv_no).strip()

        if "invoice_date" in normalized or "invoiceDate" in normalized:
            inv_date = normalized.get("invoice_date") or normalized.get("invoiceDate")
            if inv_date is not None:
                parsed = _parse_date(inv_date)
                if parsed is not None:
                    normalized["invoice_date"] = parsed.isoformat()

        if "project_id" in normalized or "projectId" in normalized:
            pid = normalized.get("project_id") or normalized.get("projectId")
            if pid is not None:
                try:
                    normalized["project_id"] = int(pid)
                except (ValueError, TypeError):
                    pass

        if "gst_rate" in normalized or "gstRate" in normalized or "gst" in normalized:
            gst_r = normalized.get("gst_rate") or normalized.get("gstRate") or normalized.get("gst")
            if gst_r is not None:
                normalized["gst_rate"] = gst_r

        if "gst_amount" in normalized or "gstAmount" in normalized:
            gst_a = normalized.get("gst_amount") or normalized.get("gstAmount")
            if gst_a is not None:
                normalized["gst_amount"] = gst_a

        if "round_off" in normalized or "roundOff" in normalized:
            ro = normalized.get("round_off") or normalized.get("roundOff")
            if ro is not None:
                normalized["round_off"] = ro

        if "net_total" in normalized or "netTotal" in normalized:
            nt = normalized.get("net_total") or normalized.get("netTotal")
            if nt is not None:
                normalized["net_total"] = nt

        if "remark" in normalized or "remarks" in normalized:
            rem = normalized.get("remark") or normalized.get("remarks")
            if rem is not None:
                normalized["remark"] = rem

        return normalized


class CustomerDeliveryInvoiceResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    invoice_no = fields.String(dump_only=True)
    invoice_number = fields.String(dump_only=True)
    invoice_date = fields.Date(dump_only=True)
    gst_rate = fields.Decimal(dump_only=True, as_string=True, places=2)
    gst_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    round_off = fields.Decimal(dump_only=True, as_string=True, places=2)
    net_total = fields.Decimal(dump_only=True, as_string=True, places=2)
    remark = fields.String(dump_only=True)
    remarks = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryInvoiceItemResponseSchema),
        dump_only=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        dump_only=True,
    )


class CustomerDeliveryInvoiceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False)
    invoice_no = fields.String(required=False)


class LatestCustomerDeliveryInvoiceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)


class LatestCustomerDeliveryInvoiceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    invoice_no = fields.String(dump_only=True)
    invoice_date = fields.Date(dump_only=True)
    net_total = fields.Decimal(as_string=True, places=2, dump_only=True)

