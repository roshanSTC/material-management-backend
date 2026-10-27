from collections.abc import Mapping
from datetime import date
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.schemas.attachment import AttachmentResponseSchema
from app.schemas.common import FlexibleDate, FlexibleFloat, FlexibleInt


class CustomerQueryItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    sr_no = FlexibleInt(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
    material_name = fields.String(required=False, allow_none=True)
    quantity = fields.Decimal(
        required=False,
        as_string=True,
        places=3,
        allow_none=True,
    )

    @pre_load
    def normalize_item(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        
        # 1. Resolve material_name from description or material_name
        name = (normalized.get("material_name") or normalized.get("description") or "").strip()
        if not name:
            sr = normalized.get("sr_no") or 1
            name = f"Material Requirement {sr}"
        normalized["material_name"] = name

        # 2. Resolve quantity
        qty = normalized.get("quantity")
        if qty is None or (isinstance(qty, str) and not qty.strip()):
            normalized["quantity"] = "1.000"
        elif isinstance(qty, (int, float)):
            normalized["quantity"] = f"{float(qty):.3f}"
        elif isinstance(qty, str):
            cleaned = qty.replace(",", "").strip()
            try:
                val = float(cleaned)
                normalized["quantity"] = f"{val:.3f}"
            except ValueError:
                normalized["quantity"] = "1.000"
        return normalized


class CustomerQueryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(
        required=True,
        validate=validate.Range(min=1),
    )

    customer_id = FlexibleInt(
        required=False,
        allow_none=True,
    )

    customer_name = fields.String(
        required=False,
        allow_none=True,
    )

    qo_date = FlexibleDate(
        required=False,
        allow_none=True,
    )

    query_date = FlexibleDate(
        required=False,
        allow_none=True,
    )

    form_code = fields.String(
        required=False,
        allow_none=True,
    )

    attachments_count = FlexibleInt(
        required=False,
        allow_none=True,
    )

    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )

    remark = fields.Raw(
        required=False,
        allow_none=True,
    )

    items = fields.List(
        fields.Nested(CustomerQueryItemSchema),
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_remarks(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        
        # 1. Date resolution (query_date vs qo_date)
        if "query_date" in normalized and not normalized.get("qo_date"):
            normalized["qo_date"] = normalized["query_date"]
        if not normalized.get("qo_date"):
            normalized["qo_date"] = date.today().isoformat()

        # 2. Remarks normalization
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        # 3. Default item if missing or empty list
        items = normalized.get("items")
        if not items:
            normalized["items"] = [{"sr_no": 1, "material_name": "General Requirement", "quantity": "1.000"}]

        return normalized


class CustomerQueryItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    material_name = fields.String(required=True)
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
    )


class CustomerQueryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    customer_name = fields.String(allow_none=True)
    qo_date = fields.Date(required=True)
    query_date = fields.Date(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)

    items = fields.List(
        fields.Nested(CustomerQueryItemResponseSchema),
        required=True,
    )

    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=True,
    )


class CustomerQueryUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=False, allow_none=True)
    customer_id = FlexibleInt(required=False, allow_none=True)
    customer_name = fields.String(required=False, allow_none=True)
    qo_date = FlexibleDate(required=False, allow_none=True)
    query_date = FlexibleDate(required=False, allow_none=True)
    form_code = fields.String(required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    remark = fields.Raw(required=False, allow_none=True)

    items = fields.List(
        fields.Nested(CustomerQueryItemSchema),
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_remarks(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        if "query_date" in normalized and not normalized.get("qo_date"):
            normalized["qo_date"] = normalized["query_date"]
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]
        return normalized


class CustomerQueryQuerySchema(Schema):
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

        return normalized


class LatestCustomerQueryQuerySchema(Schema):
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
            else normalized.get("product_id")
            if normalized.get("product_id") is not None
            else normalized.get("projectId")
            if normalized.get("projectId") is not None
            else normalized.get("productId")
        )
        if resolved_id is not None and str(resolved_id).strip() != "":
            normalized["project_id"] = str(resolved_id).strip()
        return normalized


class LatestCustomerQueryItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    material_name = fields.String(required=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)


class LatestCustomerQueryResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    items = fields.List(
        fields.Nested(LatestCustomerQueryItemResponseSchema),
        required=True,
    )
