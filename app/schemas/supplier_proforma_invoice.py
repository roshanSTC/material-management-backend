import re
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


class SupplierProformaInvoiceItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    material_name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    description = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=500),
            _not_blank,
        ),
    )
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    hsn_sac = fields.String(
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
        validate=validate.Range(min=Decimal("0.00")),
    )

    @pre_load
    def normalize_item_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Handle material_name / description fallback
        mat_name = (
            normalized.get("material_name")
            if normalized.get("material_name") is not None
            else normalized.get("materialName")
        )
        desc = (
            normalized.get("description")
            if normalized.get("description") is not None
            else normalized.get("item_description")
        )
        if not desc and mat_name:
            desc = mat_name
        if not mat_name and desc:
            mat_name = desc

        if mat_name is not None:
            normalized["material_name"] = str(mat_name).strip()
        if desc is not None:
            normalized["description"] = str(desc).strip()

        # Handle HSN aliases
        hsn = (
            normalized.get("hsn_code")
            if normalized.get("hsn_code") is not None
            else normalized.get("hsn_sac")
            if normalized.get("hsn_sac") is not None
            else normalized.get("hsn")
        )
        if hsn is not None:
            cleaned_hsn = str(hsn).strip()
            normalized["hsn_code"] = cleaned_hsn
            normalized["hsn_sac"] = cleaned_hsn

        # Quantity
        qty_val = (
            normalized.get("quantity")
            if normalized.get("quantity") is not None
            else normalized.get("qty")
        )
        if qty_val is not None:
            normalized["quantity"] = str(qty_val).strip()

        # Unit price
        price_val = (
            normalized.get("unit_price")
            if normalized.get("unit_price") is not None
            else normalized.get("unitPrice")
            if normalized.get("unitPrice") is not None
            else normalized.get("rate")
        )
        if price_val is not None:
            normalized["unit_price"] = str(price_val).strip()

        # Net amount
        net_val = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netAmount")
        )
        if net_val is not None:
            normalized["net_amount"] = str(net_val).strip()

        return normalized


class SupplierProformaInvoiceItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False)
    material_name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    description = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=500),
            _not_blank,
        ),
    )
    hsn_code = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    hsn_sac = fields.String(
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
        validate=validate.Range(min=Decimal("0.00")),
    )


class SupplierProformaInvoiceItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    proforma_invoice_id = fields.Integer(required=True)
    material_name = fields.String(allow_none=True)
    description = fields.String(required=True)
    item_description = fields.String(dump_only=True)
    hsn_code = fields.String(allow_none=True)
    hsn = fields.String(dump_only=True)
    hsn_sac = fields.String(dump_only=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, required=True)
    net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    created_at = fields.DateTime(required=True)


class SupplierProformaInvoiceCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    supplier_id = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
    )
    order_confirmation_id = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
    )
    proforma_invoice_no = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    proforma_invoice_date = fields.Date(
        required=True,
    )
    delivery_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_date = fields.Date(
        required=False,
        allow_none=True,
    )
    payment_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    warranty_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    total_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    total_net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(SupplierProformaInvoiceItemCreateSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @pre_load
    def normalize_invoice_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # Project ID
        resolved_pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_pid is not None and str(resolved_pid).strip() != "":
            normalized["project_id"] = str(resolved_pid).strip()

        # Supplier ID
        resolved_sid = (
            normalized.get("supplier_id")
            if normalized.get("supplier_id") is not None
            else normalized.get("supplierId")
        )
        if resolved_sid is not None and str(resolved_sid).strip() != "":
            normalized["supplier_id"] = str(resolved_sid).strip()

        # Order Confirmation ID
        resolved_ocid = (
            normalized.get("order_confirmation_id")
            if normalized.get("order_confirmation_id") is not None
            else normalized.get("orderConfirmationId")
        )
        if resolved_ocid is not None and str(resolved_ocid).strip() != "":
            normalized["order_confirmation_id"] = str(resolved_ocid).strip()

        # Proforma invoice number / no
        resolved_no = (
            normalized.get("proforma_invoice_no")
            if normalized.get("proforma_invoice_no") is not None
            else normalized.get("proforma_invoice_number")
            if normalized.get("proforma_invoice_number") is not None
            else normalized.get("proformaInvoiceNo")
            if normalized.get("proformaInvoiceNo") is not None
            else normalized.get("proformaInvoiceNumber")
            if normalized.get("proformaInvoiceNumber") is not None
            else normalized.get("invoice_no")
        )
        if resolved_no is not None:
            normalized["proforma_invoice_no"] = str(resolved_no).strip()

        # Proforma invoice date
        resolved_date = (
            normalized.get("proforma_invoice_date")
            if normalized.get("proforma_invoice_date") is not None
            else normalized.get("proformaInvoiceDate")
            if normalized.get("proformaInvoiceDate") is not None
            else normalized.get("invoice_date")
            if normalized.get("invoice_date") is not None
            else normalized.get("invoiceDate")
        )
        if resolved_date is not None:
            pdate = _parse_date(resolved_date)
            if pdate:
                normalized["proforma_invoice_date"] = pdate.isoformat()

        # Delivery terms
        resolved_dt = (
            normalized.get("delivery_terms")
            if normalized.get("delivery_terms") is not None
            else normalized.get("delivery_term")
            if normalized.get("delivery_term") is not None
            else normalized.get("deliveryTerms")
        )
        if resolved_dt is not None:
            normalized["delivery_terms"] = str(resolved_dt).strip()

        # Delivery period
        resolved_dp = (
            normalized.get("delivery_period")
            if normalized.get("delivery_period") is not None
            else normalized.get("deliveryPeriod")
        )
        if resolved_dp is not None:
            normalized["delivery_period"] = str(resolved_dp).strip()

        # Delivery date
        resolved_dd = (
            normalized.get("delivery_date")
            if normalized.get("delivery_date") is not None
            else normalized.get("deliveryDate")
        )
        if resolved_dd is not None:
            pdd = _parse_date(resolved_dd)
            if pdd:
                normalized["delivery_date"] = pdd.isoformat()

        # Payment terms
        resolved_pt = (
            normalized.get("payment_terms")
            if normalized.get("payment_terms") is not None
            else normalized.get("payment_term")
            if normalized.get("payment_term") is not None
            else normalized.get("paymentTerms")
        )
        if resolved_pt is not None:
            normalized["payment_terms"] = str(resolved_pt).strip()

        # Warranty period
        resolved_wp = (
            normalized.get("warranty_period")
            if normalized.get("warranty_period") is not None
            else normalized.get("warrantyPeriod")
        )
        if resolved_wp is not None:
            normalized["warranty_period"] = str(resolved_wp).strip()

        # Total amount
        resolved_total = (
            normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("totalAmount")
        )
        if resolved_total is not None:
            normalized["total_amount"] = str(resolved_total).strip()

        # Total net amount
        resolved_net_total = (
            normalized.get("total_net_amount")
            if normalized.get("total_net_amount") is not None
            else normalized.get("totalNetAmount")
        )
        if resolved_net_total is not None:
            normalized["total_net_amount"] = str(resolved_net_total).strip()

        # Remark / remarks
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class SupplierProformaInvoiceUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    supplier_id = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
    )
    order_confirmation_id = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
    )
    proforma_invoice_no = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    proforma_invoice_date = fields.Date(
        required=False,
    )
    delivery_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_date = fields.Date(
        required=False,
        allow_none=True,
    )
    payment_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    warranty_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    total_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    total_net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=Decimal("0.00")),
    )
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(SupplierProformaInvoiceItemCreateSchema),
        required=False,
    )

    @pre_load
    def normalize_update_data(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "projectId" in normalized and "project_id" not in normalized:
            normalized["project_id"] = normalized["projectId"]
        if "proforma_invoice_number" in normalized and "proforma_invoice_no" not in normalized:
            normalized["proforma_invoice_no"] = normalized["proforma_invoice_number"]
        if "invoice_date" in normalized and "proforma_invoice_date" not in normalized:
            normalized["proforma_invoice_date"] = normalized["invoice_date"]
        if "proformaInvoiceDate" in normalized and "proforma_invoice_date" not in normalized:
            normalized["proforma_invoice_date"] = normalized["proformaInvoiceDate"]
        if "delivery_term" in normalized and "delivery_terms" not in normalized:
            normalized["delivery_terms"] = normalized["delivery_term"]
        if "deliveryPeriod" in normalized and "delivery_period" not in normalized:
            normalized["delivery_period"] = normalized["deliveryPeriod"]
        if "totalAmount" in normalized and "total_amount" not in normalized:
            normalized["total_amount"] = normalized["totalAmount"]
        if "totalNetAmount" in normalized and "total_net_amount" not in normalized:
            normalized["total_net_amount"] = normalized["totalNetAmount"]
        if "remarks" in normalized and "remark" not in normalized:
            normalized["remark"] = normalized["remarks"]

        return normalized


class SupplierProformaInvoiceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, validate=validate.Range(min=1))

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        resolved_pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_pid is not None and str(resolved_pid).strip() != "":
            normalized["project_id"] = str(resolved_pid).strip()

        resolved_sid = (
            normalized.get("supplier_id")
            if normalized.get("supplier_id") is not None
            else normalized.get("supplierId")
        )
        if resolved_sid is not None and str(resolved_sid).strip() != "":
            normalized["supplier_id"] = str(resolved_sid).strip()

        resolved_no = (
            normalized.get("proforma_invoice_no")
            if normalized.get("proforma_invoice_no") is not None
            else normalized.get("proforma_invoice_number")
        )
        if resolved_no is not None and str(resolved_no).strip() != "":
            normalized["proforma_invoice_no"] = str(resolved_no).strip()

        return normalized


class SupplierProformaInvoiceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)
    order_confirmation_id = fields.Integer(allow_none=True)
    proforma_invoice_no = fields.String(required=True)
    proforma_invoice_number = fields.String(dump_only=True)
    proforma_invoice_date = fields.Date(required=True)
    invoice_date = fields.Date(dump_only=True)
    delivery_terms = fields.String(allow_none=True)
    delivery_term = fields.String(dump_only=True)
    delivery_period = fields.String(allow_none=True)
    delivery_date = fields.Date(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    payment_term = fields.String(dump_only=True)
    warranty_period = fields.String(allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    remark = fields.String(allow_none=True)
    remarks = fields.String(dump_only=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(SupplierProformaInvoiceItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=False,
    )


class LatestSupplierProformaInvoiceQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        resolved_id = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_id is not None and str(resolved_id).strip() != "":
            normalized["project_id"] = str(resolved_id).strip()
        return normalized


class LatestSupplierProformaInvoiceItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    material_name = fields.String(allow_none=True)
    description = fields.String(allow_none=True)
    hsn_code = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)


class LatestSupplierProformaInvoiceResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    items = fields.List(
        fields.Nested(LatestSupplierProformaInvoiceItemResponseSchema),
        required=True,
    )

