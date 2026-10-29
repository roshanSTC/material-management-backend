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
from app.utils.date_utils import parse_date_input


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
    parsed = parse_date_input(s)
    if parsed is not None:
        return parsed
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
        return date.fromisoformat(s)
    except Exception:
        raise ValidationError(f"Invalid date format: {val}")


class CustomerDeliveryInvoiceItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    sr_no = fields.Integer(required=False, allow_none=True)
    material_name = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
    )
    description = fields.String(required=False, allow_none=True)
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    hsn_sac = fields.String(required=False, allow_none=True)
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
    total_amount = fields.Decimal(
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

        # Handle material_name / material_description / description fallback
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
            normalized["description"] = str(mat_name).strip()

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
            normalized["hsn_sac"] = str(hsn).strip()

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

        # Handle net_amount / amount / total_amount / total_price fallback
        net_amt = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netAmount")
        )
        if net_amt is None:
            net_amt = (
                normalized.get("total_amount")
                if normalized.get("total_amount") is not None
                else normalized.get("totalAmount")
                if normalized.get("totalAmount") is not None
                else normalized.get("amount")
                if normalized.get("amount") is not None
                else normalized.get("total_price")
            )
        if net_amt is not None:
            normalized["net_amount"] = net_amt
            normalized["total_amount"] = net_amt

        return normalized


class CustomerDeliveryInvoiceItemUpdateSchema(CustomerDeliveryInvoiceItemCreateSchema):
    id = fields.Integer(required=False, allow_none=True)
    material_name = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
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


class CustomerDeliveryInvoiceItemResponseSchema(Schema):
    id = fields.Integer(dump_only=True)
    sr_no = fields.Integer(dump_only=True)
    invoice_id = fields.Integer(dump_only=True)
    material_name = fields.String(dump_only=True)
    description = fields.String(dump_only=True, attribute="material_name")
    hsn_code = fields.String(dump_only=True)
    hsn_sac = fields.String(dump_only=True, attribute="hsn_code")
    quantity = fields.Decimal(dump_only=True, as_string=True, places=3)
    unit_price = fields.Decimal(dump_only=True, as_string=True, places=2)
    net_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_amount = fields.Decimal(dump_only=True, attribute="net_amount", as_string=True, places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class CustomerDeliveryInvoiceCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=True)
    customer_name = fields.String(required=False, allow_none=True)
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
    gst_rate_pct = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    gst_pct = fields.Decimal(
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
    total_net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    total_gross_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    total_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    status = fields.String(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = fields.Integer(required=False, allow_none=True)
    remark = fields.Raw(
        required=False,
        allow_none=True,
    )
    remarks = fields.Raw(
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

        # Handle gst_rate / gst_rate_pct / gst_pct
        gst_r = (
            normalized.get("gst_rate")
            if normalized.get("gst_rate") is not None
            else normalized.get("gstRate")
            if normalized.get("gstRate") is not None
            else normalized.get("gst_rate_pct")
            if normalized.get("gst_rate_pct") is not None
            else normalized.get("gst_pct")
            if normalized.get("gst_pct") is not None
            else normalized.get("gst")
        )
        if gst_r is not None:
            normalized["gst_rate"] = str(gst_r).strip()
            normalized["gst_rate_pct"] = str(gst_r).strip()
            normalized["gst_pct"] = str(gst_r).strip()

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

        # Handle net_total (gross amount)
        nt = (
            normalized.get("total_gross_amount")
            if normalized.get("total_gross_amount") is not None
            else normalized.get("totalGrossAmount")
            if normalized.get("totalGrossAmount") is not None
            else normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("net_total")
            if normalized.get("net_total") is not None
            else normalized.get("netTotal")
        )
        if nt is not None:
            normalized["net_total"] = str(nt).strip()
            normalized["total_gross_amount"] = str(nt).strip()
            normalized["total_amount"] = str(nt).strip()

        # Handle total_net_amount
        t_net = (
            normalized.get("total_net_amount")
            if normalized.get("total_net_amount") is not None
            else normalized.get("totalNetAmount")
        )
        if t_net is not None:
            normalized["total_net_amount"] = str(t_net).strip()

        # Handle remark / remarks
        rem = (
            normalized.get("remarks")
            if normalized.get("remarks") is not None
            else normalized.get("remark")
        )
        if rem is not None:
            normalized["remark"] = rem

        return normalized


class CustomerDeliveryInvoiceUpdateSchema(CustomerDeliveryInvoiceCreateSchema):
    project_id = fields.Integer(required=False, allow_none=True)
    invoice_no = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=100),
    )
    invoice_date = fields.Date(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerDeliveryInvoiceItemUpdateSchema),
        required=False,
        allow_none=True,
    )


class CustomerDeliveryInvoiceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    project_id = fields.Integer(dump_only=True)
    customer_name = fields.String(dump_only=True)
    invoice_no = fields.String(dump_only=True)
    invoice_number = fields.String(dump_only=True)
    invoice_date = fields.Date(dump_only=True)
    gst_rate = fields.Decimal(dump_only=True, as_string=True, places=2)
    gst_rate_pct = fields.Decimal(dump_only=True, as_string=True, places=2)
    gst_pct = fields.Decimal(dump_only=True, as_string=True, places=2)
    gst_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    round_off = fields.Decimal(dump_only=True, as_string=True, places=2)
    net_total = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    total_amount = fields.Decimal(dump_only=True, as_string=True, places=2)
    form_code = fields.String(dump_only=True)
    status = fields.String(dump_only=True)
    attachments_count = fields.Integer(dump_only=True)
    remarks = fields.Raw(dump_only=True)
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
