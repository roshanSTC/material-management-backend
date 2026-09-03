import re
from decimal import Decimal

from marshmallow import Schema, ValidationError, fields, pre_load, validate, validates_schema

from app.schemas.attachment import AttachmentResponseSchema


def _not_blank(value: str) -> None:
    if not value.strip():
        raise ValidationError("Field must not be blank.")


def _parse_quotation_value_and_unit(raw_val, explicit_unit=None):
    if raw_val is None:
        return None, explicit_unit
    if isinstance(raw_val, (int, float, Decimal)):
        return Decimal(str(raw_val)), explicit_unit

    s = str(raw_val).strip()
    match = re.search(r"[-+]?(?:\d*\.\d+|\d+)", s)
    if not match:
        raise ValidationError("quotation_value must contain a valid number.")

    num_str = match.group(0)
    extracted_unit = (s[:match.start()] + s[match.end():]).strip()
    final_unit = explicit_unit if explicit_unit else (extracted_unit or None)
    return Decimal(num_str), final_unit


class SupplierQuotationItemSchema(Schema):
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

    @pre_load
    def normalize_item(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "unit_price" in normalized and normalized["unit_price"] is not None:
            normalized["unit_price"] = str(normalized["unit_price"]).strip()
        if "net_amount" in normalized and normalized["net_amount"] is not None:
            normalized["net_amount"] = str(normalized["net_amount"]).strip()
        return normalized


class SupplierQuotationCreateSchema(Schema):
    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    supplier_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    quotation_number = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    quotation_date = fields.Date(required=True)
    quotation_value = fields.Decimal(
        required=True,
        as_string=True,
        places=2,
        validate=validate.Range(min=0.01),
    )
    currency_unit = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=20),
    )
    validity = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    incoterms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    payment_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    delivery_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    remark = fields.String(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierQuotationItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @pre_load
    def normalize_quotation(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        explicit_unit = normalized.get("currency_unit") or normalized.get("value_symbol")
        if "quotation_value" in normalized and normalized["quotation_value"] is not None:
            val, unit = _parse_quotation_value_and_unit(
                normalized["quotation_value"],
                explicit_unit,
            )
            normalized["quotation_value"] = str(val)
            if unit:
                normalized["currency_unit"] = unit
        elif explicit_unit:
            normalized["currency_unit"] = explicit_unit
        return normalized


class SupplierQuotationUpdateSchema(Schema):
    project_id = fields.Integer(validate=validate.Range(min=1))
    supplier_id = fields.Integer(validate=validate.Range(min=1))
    quotation_number = fields.String(
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    quotation_date = fields.Date()
    quotation_value = fields.Decimal(
        as_string=True,
        places=2,
        validate=validate.Range(min=0.01),
    )
    currency_unit = fields.String(
        allow_none=True,
        validate=validate.Length(max=20),
    )
    validity = fields.String(allow_none=True, validate=validate.Length(max=100))
    incoterms = fields.String(allow_none=True, validate=validate.Length(max=50))
    payment_terms = fields.String(allow_none=True, validate=validate.Length(max=255))
    delivery_period = fields.String(
        allow_none=True,
        validate=validate.Length(max=100),
    )
    remark = fields.String(allow_none=True)
    items = fields.List(
        fields.Nested(SupplierQuotationItemSchema),
        validate=validate.Length(min=1),
    )

    @pre_load
    def normalize_quotation(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        explicit_unit = normalized.get("currency_unit") or normalized.get("value_symbol")
        if "quotation_value" in normalized and normalized["quotation_value"] is not None:
            val, unit = _parse_quotation_value_and_unit(
                normalized["quotation_value"],
                explicit_unit,
            )
            normalized["quotation_value"] = str(val)
            if unit:
                normalized["currency_unit"] = unit
        elif explicit_unit:
            normalized["currency_unit"] = explicit_unit
        return normalized

    @validates_schema
    def validate_non_empty_payload(self, data, **kwargs):
        if not data:
            raise ValidationError(
                "At least one supplier quotation field is required."
            )


class SupplierQuotationItemResponseSchema(Schema):
    id = fields.Integer(required=True)
    material_name = fields.String(required=True)
    quantity = fields.Decimal(required=True, as_string=True, places=3)
    unit_price = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)


class SupplierQuotationResponseSchema(Schema):
    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)
    quotation_number = fields.String(required=True)
    quotation_date = fields.Date(required=True)
    quotation_value = fields.Decimal(required=True, as_string=True, places=2)
    currency_unit = fields.String(allow_none=True)
    validity = fields.String(allow_none=True)
    incoterms = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    remark = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(fields.Nested(SupplierQuotationItemResponseSchema), required=True)
    attachments = fields.List(fields.Nested(AttachmentResponseSchema), required=True)
