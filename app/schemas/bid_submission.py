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


class BidSubmissionItemCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    description = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=500),
            _not_blank,
        ),
    )
    hsn_sac = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    unit_price = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    quantity = fields.Decimal(
        required=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    net_total = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )

    @pre_load
    def normalize_item(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        if "material_name" in normalized and not normalized.get("description"):
            normalized["description"] = normalized["material_name"]
        if "net_amount" in normalized and not normalized.get("net_total"):
            normalized["net_total"] = normalized["net_amount"]
        if "quantity" in normalized and normalized["quantity"] is not None:
            normalized["quantity"] = str(normalized["quantity"]).strip()
        if "unit_price" in normalized and normalized["unit_price"] is not None:
            normalized["unit_price"] = str(normalized["unit_price"]).strip()
        if "net_total" in normalized and normalized["net_total"] is not None:
            normalized["net_total"] = str(normalized["net_total"]).strip()
        return normalized


class BidSubmissionItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=500),
    )
    hsn_sac = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=50),
    )
    unit_price = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    quantity = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    net_total = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )

    @pre_load
    def normalize_item(self, data, **kwargs):
        if not isinstance(data, (dict, Mapping)):
            return data
        normalized = dict(data)
        if "material_name" in normalized and not normalized.get("description"):
            normalized["description"] = normalized["material_name"]
        if "net_amount" in normalized and not normalized.get("net_total"):
            normalized["net_total"] = normalized["net_amount"]
        if "quantity" in normalized and normalized["quantity"] is not None:
            normalized["quantity"] = str(normalized["quantity"]).strip()
        if "unit_price" in normalized and normalized["unit_price"] is not None:
            normalized["unit_price"] = str(normalized["unit_price"]).strip()
        if "net_total" in normalized and normalized["net_total"] is not None:
            normalized["net_total"] = str(normalized["net_total"]).strip()
        return normalized


class BidSubmissionCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    tender_id = fields.Integer(
        required=False,
        allow_none=True,
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
    submission_date = fields.Raw(
        required=False,
        allow_none=True,
    )
    delivery_term = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    payment_term = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    validity = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    warranty_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    gst_rate = fields.Decimal(
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
        fields.Nested(BidSubmissionItemCreateSchema),
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

        # tender_id
        resolved_tid = (
            normalized.get("tender_id")
            if normalized.get("tender_id") is not None
            else normalized.get("tenderId")
            if normalized.get("tenderId") is not None
            else normalized.get("customer_tender_id")
            if normalized.get("customer_tender_id") is not None
            else normalized.get("customerTenderId")
        )
        if resolved_tid is not None and str(resolved_tid).strip() != "":
            normalized["tender_id"] = resolved_tid

        # tender_title / tender_name
        if "tender_name" in normalized and not normalized.get("tender_title"):
            normalized["tender_title"] = normalized["tender_name"]
        elif "tenderTitle" in normalized and not normalized.get("tender_title"):
            normalized["tender_title"] = normalized["tenderTitle"]

        # tender_number / submission_number
        if "submission_number" in normalized and not normalized.get("tender_number"):
            normalized["tender_number"] = normalized["submission_number"]
        elif "tenderNumber" in normalized and not normalized.get("tender_number"):
            normalized["tender_number"] = normalized["tenderNumber"]
        elif "submissionNumber" in normalized and not normalized.get("tender_number"):
            normalized["tender_number"] = normalized["submissionNumber"]

        # delivery_term / delivery_terms
        if "delivery_terms" in normalized and not normalized.get("delivery_term"):
            normalized["delivery_term"] = normalized["delivery_terms"]
        elif "deliveryTerms" in normalized and not normalized.get("delivery_term"):
            normalized["delivery_term"] = normalized["deliveryTerms"]

        # delivery_period / period / deliveryPeriod
        if "deliveryPeriod" in normalized and not normalized.get("delivery_period"):
            normalized["delivery_period"] = normalized["deliveryPeriod"]
        elif "period" in normalized and not normalized.get("delivery_period"):
            normalized["delivery_period"] = normalized["period"]
        if "delivery_period" in normalized and not normalized.get("period"):
            normalized["period"] = normalized["delivery_period"]

        # payment_term / payment_terms
        if "payment_terms" in normalized and not normalized.get("payment_term"):
            normalized["payment_term"] = normalized["payment_terms"]
        elif "paymentTerms" in normalized and not normalized.get("payment_term"):
            normalized["payment_term"] = normalized["paymentTerms"]

        # warranty_period / warrantyPeriod
        if "warrantyPeriod" in normalized and not normalized.get("warranty_period"):
            normalized["warranty_period"] = normalized["warrantyPeriod"]

        # submission_date / submissionDate
        if "submissionDate" in normalized and not normalized.get("submission_date"):
            normalized["submission_date"] = normalized["submissionDate"]

        # gst_rate decimal
        if "gst_rate" in normalized and normalized["gst_rate"] is not None:
            normalized["gst_rate"] = str(normalized["gst_rate"]).strip()
        elif "gstRate" in normalized and normalized["gstRate"] is not None:
            normalized["gst_rate"] = str(normalized["gstRate"]).strip()

        # remarks alias
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]

        return normalized


class BidSubmissionUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)
    tender_id = fields.Integer(required=False, allow_none=True)
    tender_title = fields.String(required=False, allow_none=True)
    tender_number = fields.String(required=False, allow_none=True)
    submission_date = fields.Raw(required=False, allow_none=True)
    delivery_term = fields.String(required=False, allow_none=True)
    delivery_period = fields.String(required=False, allow_none=True)
    period = fields.String(required=False, allow_none=True)
    payment_term = fields.String(required=False, allow_none=True)
    validity = fields.String(required=False, allow_none=True)
    warranty_period = fields.String(required=False, allow_none=True)
    gst_rate = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remark = fields.String(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(BidSubmissionItemUpdateSchema),
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
        if "tenderId" in normalized and "tender_id" not in normalized:
            normalized["tender_id"] = normalized["tenderId"]
        if "customer_tender_id" in normalized and "tender_id" not in normalized:
            normalized["tender_id"] = normalized["customer_tender_id"]
        if "tender_name" in normalized and not normalized.get("tender_title"):
            normalized["tender_title"] = normalized["tender_name"]
        if "submission_number" in normalized and not normalized.get("tender_number"):
            normalized["tender_number"] = normalized["submission_number"]
        if "delivery_terms" in normalized and not normalized.get("delivery_term"):
            normalized["delivery_term"] = normalized["delivery_terms"]
        if "deliveryPeriod" in normalized and not normalized.get("delivery_period"):
            normalized["delivery_period"] = normalized["deliveryPeriod"]
        elif "period" in normalized and not normalized.get("delivery_period"):
            normalized["delivery_period"] = normalized["period"]
        if "delivery_period" in normalized and not normalized.get("period"):
            normalized["period"] = normalized["delivery_period"]
        if "payment_terms" in normalized and not normalized.get("payment_term"):
            normalized["payment_term"] = normalized["payment_terms"]
        if "warrantyPeriod" in normalized and not normalized.get("warranty_period"):
            normalized["warranty_period"] = normalized["warrantyPeriod"]
        if "submissionDate" in normalized and not normalized.get("submission_date"):
            normalized["submission_date"] = normalized["submissionDate"]
        if "gst_rate" in normalized and normalized["gst_rate"] is not None:
            normalized["gst_rate"] = str(normalized["gst_rate"]).strip()
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]

        return normalized


class BidSubmissionQuerySchema(Schema):
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


class BidSubmissionItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    bid_submission_id = fields.Integer(required=True)
    description = fields.String(required=True)
    material_name = fields.String(attribute="description", required=True, dump_only=True)
    hsn_sac = fields.String(allow_none=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    net_total = fields.Decimal(as_string=True, places=2, allow_none=True)
    net_amount = fields.Decimal(attribute="net_total", as_string=True, places=2, allow_none=True, dump_only=True)
    created_at = fields.DateTime(required=True)


class BidSubmissionResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    tender_id = fields.Integer(allow_none=True)
    tender_title = fields.String(allow_none=True)
    tender_name = fields.String(attribute="tender_title", allow_none=True, dump_only=True)
    submission_date = fields.DateTime(allow_none=True)
    tender_number = fields.String(required=True)
    submission_number = fields.String(attribute="tender_number", allow_none=True, dump_only=True)
    delivery_term = fields.String(allow_none=True)
    delivery_terms = fields.String(attribute="delivery_term", allow_none=True, dump_only=True)
    delivery_period = fields.String(allow_none=True)
    period = fields.String(attribute="delivery_period", allow_none=True, dump_only=True)
    payment_term = fields.String(allow_none=True)
    payment_terms = fields.String(attribute="payment_term", allow_none=True, dump_only=True)
    validity = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    gst_rate = fields.Decimal(as_string=True, places=2, allow_none=True)
    remark = fields.String(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(BidSubmissionItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=False,
    )

