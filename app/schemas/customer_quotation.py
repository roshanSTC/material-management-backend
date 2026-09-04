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
    if isinstance(val, date):
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


def _parse_decimal(val):
    if val is None:
        return None
    if isinstance(val, (int, float, Decimal)):
        return Decimal(str(val))
    s = str(val).strip()
    if not s:
        return None
    match = re.search(r"[-+]?(?:\d*\.\d+|\d+)", s)
    if not match:
        raise ValidationError("Must contain a valid number.")
    return Decimal(match.group(0))


class CustomerQuotationItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    cost_sheet_item_id = fields.Integer(
        required=False,
        allow_none=True,
    )
    quotation_number = fields.String(
        required=False,
        allow_none=True,
    )
    item_code = fields.String(
        required=False,
        allow_none=True,
    )
    material_name = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
    )
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=0.001),
    )
    unit_price = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )
    net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0),
    )
    customs_duty_rate = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0),
    )

    @pre_load
    def normalize_item(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "unit_price" in normalized and normalized["unit_price"] is not None:
            normalized["unit_price"] = str(normalized["unit_price"]).strip()
        if "net_amount" in normalized and normalized["net_amount"] is not None:
            normalized["net_amount"] = str(normalized["net_amount"]).strip()
        if "quantity" in normalized and normalized["quantity"] is not None:
            normalized["quantity"] = str(normalized["quantity"]).strip()
        return normalized


class CustomerQuotationCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    customer_id = fields.Integer(
        required=False,
        allow_none=True,
    )
    quotation_number = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    quotation_date = fields.Raw(
        required=True,
    )
    quotation_value = fields.Raw(
        required=True,
    )
    currency_unit = fields.String(
        required=False,
        allow_none=True,
    )
    currency_symbol = fields.String(
        required=False,
        allow_none=True,
    )
    total_net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    validity = fields.String(
        required=False,
        allow_none=True,
    )
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(CustomerQuotationItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @pre_load
    def normalize_payload(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "qo_number" in normalized and "quotation_number" not in normalized:
            normalized["quotation_number"] = normalized["qo_number"]
        if "remarks" in normalized and "remark" not in normalized:
            normalized["remark"] = normalized["remarks"]
        if "total_net_amount" in normalized and normalized["total_net_amount"] is not None:
            normalized["total_net_amount"] = str(normalized["total_net_amount"]).strip()
        return normalized


class CustomerQuotationUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    customer_id = fields.Integer(
        required=False,
        allow_none=True,
    )
    quotation_number = fields.String(
        required=False,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    quotation_date = fields.Raw(
        required=False,
    )
    quotation_value = fields.Raw(
        required=False,
    )
    currency_unit = fields.String(
        required=False,
        allow_none=True,
    )
    currency_symbol = fields.String(
        required=False,
        allow_none=True,
    )
    total_net_amount = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    validity = fields.String(
        required=False,
        allow_none=True,
    )
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(CustomerQuotationItemSchema),
        required=False,
    )

    @pre_load
    def normalize_payload(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "qo_number" in normalized and "quotation_number" not in normalized:
            normalized["quotation_number"] = normalized["qo_number"]
        if "remarks" in normalized and "remark" not in normalized:
            normalized["remark"] = normalized["remarks"]
        if "total_net_amount" in normalized and normalized["total_net_amount"] is not None:
            normalized["total_net_amount"] = str(normalized["total_net_amount"]).strip()
        return normalized


class CustomerQuotationQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    customer_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    quotation_number = fields.String(
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        resolved_id = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("product_id")
            if normalized.get("product_id") is not None
            else normalized.get("projectId")
            if normalized.get("projectId") is not None
            else normalized.get("productId")
        )
        if resolved_id is not None and str(resolved_id).strip() != "":
            normalized["project_id"] = str(resolved_id).strip()
        else:
            normalized.pop("project_id", None)
            normalized.pop("projectId", None)
            normalized.pop("product_id", None)
            normalized.pop("productId", None)

        resolved_cust = (
            normalized.get("customer_id")
            if normalized.get("customer_id") is not None
            else normalized.get("customerId")
        )
        if resolved_cust is not None and str(resolved_cust).strip() != "":
            normalized["customer_id"] = str(resolved_cust).strip()
        else:
            normalized.pop("customer_id", None)
            normalized.pop("customerId", None)

        resolved_q = (
            normalized.get("quotation_number")
            if normalized.get("quotation_number") is not None
            else normalized.get("quotationNumber")
            if normalized.get("quotationNumber") is not None
            else normalized.get("qo_number")
        )
        if resolved_q is not None and str(resolved_q).strip() != "":
            normalized["quotation_number"] = str(resolved_q).strip()
        else:
            normalized.pop("quotation_number", None)
            normalized.pop("quotationNumber", None)
            normalized.pop("qo_number", None)

        return normalized
    

class CustomerQuotationItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    customer_quotation_id = fields.Integer(required=True)
    cost_sheet_item_id = fields.Integer(allow_none=True)
    quotation_number = fields.String(allow_none=True)
    item_code = fields.String(allow_none=True)
    material_name = fields.String(required=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    customs_duty_rate = fields.Float(allow_none=True)
    created_at = fields.DateTime(required=True)


class CustomerQuotationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    quotation_number = fields.String(required=True)
    qo_number = fields.String(allow_none=True)
    quotation_date = fields.Date(required=True)
    quotation_value = fields.Decimal(as_string=True, places=2, required=True)
    currency_unit = fields.String(allow_none=True)
    currency_symbol = fields.String(allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    validity = fields.String(allow_none=True)
    remark = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(CustomerQuotationItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=True,
    )

