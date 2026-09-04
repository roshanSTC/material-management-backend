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


def _parse_datetime(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    s = str(val).strip()
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s)
    except Exception:
        raise ValidationError(f"Invalid datetime format: {val}")


class CustomerTenderItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    item_code = fields.String(
        required=False,
        allow_none=True,
    )
    description = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=500),
            _not_blank,
        ),
    )
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )

    @pre_load
    def normalize_item(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        if "material_name" in normalized and not normalized.get("description"):
            normalized["description"] = normalized["material_name"]
        if "quantity" in normalized and normalized["quantity"] is not None:
            normalized["quantity"] = str(normalized["quantity"]).strip()
        if "item_code" in normalized and normalized["item_code"] is not None:
            normalized["item_code"] = str(normalized["item_code"]).strip()
        return normalized


class CustomerTenderItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    item_code = fields.String(required=False, allow_none=True)
    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=500),
    )
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )

    @pre_load
    def normalize_item(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        if "material_name" in normalized and not normalized.get("description"):
            normalized["description"] = normalized["material_name"]
        if "quantity" in normalized and normalized["quantity"] is not None:
            normalized["quantity"] = str(normalized["quantity"]).strip()
        if "item_code" in normalized and normalized["item_code"] is not None:
            normalized["item_code"] = str(normalized["item_code"]).strip()
        return normalized


class CustomerTenderCreateSchema(Schema):
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
    officer_name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    email = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    address = fields.String(
        required=False,
        allow_none=True,
    )
    website = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=2048),
    )
    contact_number = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=30),
    )
    tender_title = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    tender_number = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    tender_date = fields.Raw(
        required=False,
        allow_none=True,
    )
    opening_date_time = fields.Raw(
        required=False,
        allow_none=True,
    )
    closing_date_time = fields.Raw(
        required=False,
        allow_none=True,
    )
    tender_fee = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    validity = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    delivery_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
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
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(CustomerTenderItemCreateSchema),
        required=False,
        load_default=list,
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        # project_id
        resolved_pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_pid is not None and str(resolved_pid).strip() != "":
            normalized["project_id"] = resolved_pid

        # customer_id
        resolved_cid = (
            normalized.get("customer_id")
            if normalized.get("customer_id") is not None
            else normalized.get("customerId")
        )
        if resolved_cid is not None and str(resolved_cid).strip() != "":
            normalized["customer_id"] = resolved_cid

        # officer_name / company_business_name
        if "company_business_name" in normalized and not normalized.get("officer_name"):
            normalized["officer_name"] = normalized["company_business_name"]

        # delivery_terms / incoterms
        if "incoterms" in normalized and not normalized.get("delivery_terms"):
            normalized["delivery_terms"] = normalized["incoterms"]

        # tender_fee decimal string
        if "tender_fee" in normalized and normalized["tender_fee"] is not None:
            normalized["tender_fee"] = str(normalized["tender_fee"]).strip()

        # remarks alias
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]

        return normalized


class CustomerTenderUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)
    customer_id = fields.Integer(required=False, allow_none=True)
    officer_name = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    address = fields.String(required=False, allow_none=True)
    website = fields.String(required=False, allow_none=True)
    contact_number = fields.String(required=False, allow_none=True)
    tender_title = fields.String(required=False, allow_none=True)
    tender_number = fields.String(required=False, allow_none=True)
    tender_date = fields.Raw(required=False, allow_none=True)
    opening_date_time = fields.Raw(required=False, allow_none=True)
    closing_date_time = fields.Raw(required=False, allow_none=True)
    tender_fee = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    validity = fields.String(required=False, allow_none=True)
    delivery_terms = fields.String(required=False, allow_none=True)
    delivery_period = fields.String(required=False, allow_none=True)
    payment_terms = fields.String(required=False, allow_none=True)
    warranty_period = fields.String(required=False, allow_none=True)
    remark = fields.String(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(CustomerTenderItemUpdateSchema),
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)

        if "projectId" in normalized and "project_id" not in normalized:
            normalized["project_id"] = normalized["projectId"]
        if "customerId" in normalized and "customer_id" not in normalized:
            normalized["customer_id"] = normalized["customerId"]
        if "company_business_name" in normalized and not normalized.get("officer_name"):
            normalized["officer_name"] = normalized["company_business_name"]
        if "incoterms" in normalized and not normalized.get("delivery_terms"):
            normalized["delivery_terms"] = normalized["incoterms"]
        if "tender_fee" in normalized and normalized["tender_fee"] is not None:
            normalized["tender_fee"] = str(normalized["tender_fee"]).strip()
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]

        return normalized


class CustomerTenderQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
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
        else:
            normalized.pop("project_id", None)
            normalized.pop("projectId", None)
        return normalized


class CustomerTenderItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    customer_tender_id = fields.Integer(required=True)
    item_code = fields.String(allow_none=True)
    description = fields.String(required=True)
    material_name = fields.String(attribute="description", required=True, dump_only=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    created_at = fields.DateTime(required=True)


class CustomerTenderResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(allow_none=True)
    officer_name = fields.String(allow_none=True)
    company_business_name = fields.String(attribute="officer_name", allow_none=True, dump_only=True)
    email = fields.String(allow_none=True)
    address = fields.String(allow_none=True)
    website = fields.String(allow_none=True)
    contact_number = fields.String(allow_none=True)
    tender_title = fields.String(allow_none=True)
    tender_number = fields.String(required=True)
    tender_date = fields.DateTime(allow_none=True)
    opening_date_time = fields.DateTime(allow_none=True)
    closing_date_time = fields.DateTime(allow_none=True)
    tender_fee = fields.Decimal(as_string=True, places=2, allow_none=True)
    validity = fields.String(allow_none=True)
    delivery_terms = fields.String(allow_none=True)
    incoterms = fields.String(attribute="delivery_terms", allow_none=True, dump_only=True)
    delivery_period = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    remark = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(CustomerTenderItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=False,
    )
