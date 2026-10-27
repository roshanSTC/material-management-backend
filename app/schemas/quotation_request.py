from collections.abc import Mapping
from datetime import date
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.schemas.common import FlexibleDate, FlexibleFloat, FlexibleInt


class QuotationRequestItemSchema(Schema):
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
        desc = (normalized.get("material_name") or normalized.get("description") or "").strip()
        if not desc:
            sr = normalized.get("sr_no") or 1
            desc = f"Item {sr}"
        normalized["material_name"] = desc

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


class QuotationRequestCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = FlexibleInt(required=True)
    supplier_id = FlexibleInt(required=False, allow_none=True)
    supplier_name = fields.String(required=False, allow_none=True)

    quotation_requested_date = FlexibleDate(required=False, allow_none=True)
    rfq_date = FlexibleDate(required=False, allow_none=True)
    supplier_contacted = fields.Boolean(required=False, allow_none=True)

    form_code = fields.String(required=False, allow_none=True)
    attachments_count = FlexibleInt(required=False, allow_none=True)

    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )

    remark = fields.Raw(
        required=False,
        allow_none=True,
    )

    items = fields.List(
        fields.Nested(QuotationRequestItemSchema),
        required=False,
        allow_none=True,
    )

    @pre_load
    def normalize_remarks(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        if "rfq_date" in normalized and not normalized.get("quotation_requested_date"):
            normalized["quotation_requested_date"] = normalized["rfq_date"]
        if not normalized.get("quotation_requested_date"):
            normalized["quotation_requested_date"] = date.today().isoformat()

        if normalized.get("supplier_contacted") is None:
            normalized["supplier_contacted"] = True

        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        items = normalized.get("items")
        if not items:
            normalized["items"] = [{"sr_no": 1, "material_name": "General RFQ Item", "quantity": "1.000"}]
        return normalized


class QuotationRequestResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    project_id = fields.Integer()
    supplier_id = fields.Integer()
    supplier_name = fields.String(allow_none=True)

    quotation_requested_date = fields.Date()
    rfq_date = fields.Date(allow_none=True)
    supplier_contacted = fields.Boolean()

    remarks = fields.Raw(
        allow_none=True
    )

    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    items = fields.List(
        fields.Nested(
            QuotationRequestItemSchema
        )
    )

    attachments = fields.List(
        fields.Dict()
    )


class QuotationRequestQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        validate=validate.Range(min=1),
    )
    supplier_id = fields.Integer(
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

        resolved_supp = (
            normalized.get("supplier_id")
            if normalized.get("supplier_id") is not None
            else normalized.get("supplierId")
        )
        if resolved_supp is not None and str(resolved_supp).strip() != "":
            normalized["supplier_id"] = str(resolved_supp).strip()
        else:
            normalized.pop("supplier_id", None)
            normalized.pop("supplierId", None)

        return normalized
