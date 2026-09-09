from collections.abc import Mapping
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate


class QuotationRequestItemSchema(Schema):
    material_name = fields.String(required=True)
    quantity = fields.Decimal(
        required=True,
        as_string=True,
    )


class QuotationRequestCreateSchema(Schema):
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=True)

    quotation_requested_date = fields.Date(
        required=True
    )

    supplier_contacted = fields.Boolean(
        required=True
    )

    remarks = fields.String(
        required=False,
        allow_none=True,
    )

    items = fields.List(
        fields.Nested(QuotationRequestItemSchema),
        required=True,
    )


class QuotationRequestResponseSchema(Schema):
    id = fields.Integer()
    project_id = fields.Integer()
    supplier_id = fields.Integer()

    quotation_requested_date = fields.Date()
    supplier_contacted = fields.Boolean()

    remarks = fields.String(
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