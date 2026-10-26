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

        # description fallback
        desc = (
            normalized.get("description")
            or normalized.get("material_name")
            or normalized.get("item_name")
            or normalized.get("material_description")
        )
        if desc is None or not str(desc).strip():
            sr_no = normalized.get("sr_no") or 1
            desc = f"Bid Item {sr_no}"
        normalized["description"] = str(desc).strip()

        # hsn_sac
        if "hsn_sac" in normalized:
            hsn = normalized.get("hsn_sac")
            normalized["hsn_sac"] = str(hsn).strip() if hsn is not None and str(hsn).strip() else None

        # quantity
        qty = (
            normalized.get("quantity")
            if normalized.get("quantity") is not None
            else normalized.get("qty")
        )
        if qty is None or str(qty).strip() == "":
            normalized["quantity"] = "1.000"
        else:
            try:
                clean_q = re.sub(r"[^\d.]", "", str(qty))
                d_q = Decimal(clean_q) if clean_q else Decimal("1.000")
                if d_q <= 0:
                    d_q = Decimal("1.000")
                normalized["quantity"] = str(d_q)
            except Exception:
                normalized["quantity"] = "1.000"

        # unit_price
        uprice = (
            normalized.get("unit_price")
            if normalized.get("unit_price") is not None
            else normalized.get("unitPrice")
            if normalized.get("unitPrice") is not None
            else normalized.get("rate")
            if normalized.get("rate") is not None
            else normalized.get("price")
        )
        if uprice is None or str(uprice).strip() == "":
            normalized["unit_price"] = None
        else:
            try:
                clean_p = re.sub(r"[^\d.]", "", str(uprice))
                normalized["unit_price"] = str(Decimal(clean_p)) if clean_p else None
            except Exception:
                normalized["unit_price"] = None

        # net_total
        total = (
            normalized.get("net_total")
            if normalized.get("net_total") is not None
            else normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netTotal")
            if normalized.get("netTotal") is not None
            else normalized.get("netAmount")
            if normalized.get("netAmount") is not None
            else normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("totalAmount")
            if normalized.get("totalAmount") is not None
            else normalized.get("total")
        )
        if total is None or str(total).strip() == "":
            normalized["net_total"] = None
        else:
            try:
                clean_t = re.sub(r"[^\d.]", "", str(total))
                normalized["net_total"] = str(Decimal(clean_t)) if clean_t else None
            except Exception:
                normalized["net_total"] = None

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
        if "description" in normalized or "material_name" in normalized:
            desc = normalized.get("description") or normalized.get("material_name")
            if desc is not None and str(desc).strip():
                normalized["description"] = str(desc).strip()
            else:
                normalized["description"] = None

        if "hsn_sac" in normalized:
            hsn = normalized.get("hsn_sac")
            normalized["hsn_sac"] = str(hsn).strip() if hsn is not None and str(hsn).strip() else None

        if "quantity" in normalized:
            qty = normalized.get("quantity")
            if qty is None or str(qty).strip() == "":
                normalized["quantity"] = None
            else:
                try:
                    clean_q = re.sub(r"[^\d.]", "", str(qty))
                    d_q = Decimal(clean_q) if clean_q else Decimal("1.000")
                    normalized["quantity"] = str(d_q)
                except Exception:
                    normalized["quantity"] = "1.000"

        if "unit_price" in normalized:
            uprice = normalized.get("unit_price")
            if uprice is None or str(uprice).strip() == "":
                normalized["unit_price"] = None
            else:
                try:
                    clean_p = re.sub(r"[^\d.]", "", str(uprice))
                    normalized["unit_price"] = str(Decimal(clean_p)) if clean_p else None
                except Exception:
                    normalized["unit_price"] = None

        total = (
            normalized.get("net_total")
            if normalized.get("net_total") is not None
            else normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netTotal")
            if normalized.get("netTotal") is not None
            else normalized.get("netAmount")
            if normalized.get("netAmount") is not None
            else normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("totalAmount")
            if normalized.get("totalAmount") is not None
            else normalized.get("total")
        )
        if total is not None:
            if str(total).strip() == "":
                normalized["net_total"] = None
            else:
                try:
                    clean_t = re.sub(r"[^\d.]", "", str(total))
                    normalized["net_total"] = str(Decimal(clean_t)) if clean_t else None
                except Exception:
                    normalized["net_total"] = None
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
    remark = fields.Raw(
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

        # tender_number / tender_no / submission_number
        tender_num = (
            normalized.get("tender_number")
            or normalized.get("tender_no")
            or normalized.get("tenderNo")
            or normalized.get("tenderNumber")
            or normalized.get("submission_number")
            or normalized.get("submissionNumber")
            or normalized.get("tender_id")
        )
        if tender_num is not None and str(tender_num).strip() != "":
            normalized["tender_number"] = str(tender_num).strip()

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

        # validity / bid_validity / quotation_validity
        val = (
            normalized.get("validity")
            or normalized.get("bid_validity")
            or normalized.get("bidValidity")
            or normalized.get("quotation_validity")
            or normalized.get("quotationValidity")
        )
        if val is not None and str(val).strip() != "":
            normalized["validity"] = str(val).strip()

        # submission_date / bid_submission_date / tender_issue_date
        sub_date = (
            normalized.get("submission_date")
            or normalized.get("submissionDate")
            or normalized.get("bid_submission_date")
            or normalized.get("bidSubmissionDate")
            or normalized.get("tender_issue_date")
            or normalized.get("tenderIssueDate")
        )
        if sub_date is not None and str(sub_date).strip() != "":
            normalized["submission_date"] = sub_date

        # gst_rate decimal / gst_pct
        gst = (
            normalized.get("gst_rate")
            if normalized.get("gst_rate") is not None
            else normalized.get("gstRate")
            if normalized.get("gstRate") is not None
            else normalized.get("gst_pct")
            if normalized.get("gst_pct") is not None
            else normalized.get("gstPct")
        )
        if gst is not None and str(gst).strip() != "":
            try:
                clean_gst = re.sub(r"[^\d.]", "", str(gst))
                normalized["gst_rate"] = str(Decimal(clean_gst)) if clean_gst else str(gst).strip()
            except Exception:
                normalized["gst_rate"] = str(gst).strip()
        else:
            normalized.pop("gst_rate", None)

        # remarks alias
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]

        # items list cleaning
        if "items" in normalized and isinstance(normalized["items"], list):
            normalized["items"] = [
                item for item in normalized["items"] if isinstance(item, (dict, Mapping))
            ]

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
    remark = fields.Raw(required=False, allow_none=True)
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

        tender_num = (
            normalized.get("tender_number")
            or normalized.get("tender_no")
            or normalized.get("tenderNo")
            or normalized.get("tenderNumber")
            or normalized.get("submission_number")
            or normalized.get("submissionNumber")
        )
        if tender_num is not None and str(tender_num).strip() != "":
            normalized["tender_number"] = str(tender_num).strip()

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

        val = (
            normalized.get("validity")
            or normalized.get("bid_validity")
            or normalized.get("bidValidity")
            or normalized.get("quotation_validity")
            or normalized.get("quotationValidity")
        )
        if val is not None and str(val).strip() != "":
            normalized["validity"] = str(val).strip()

        sub_date = (
            normalized.get("submission_date")
            or normalized.get("submissionDate")
            or normalized.get("bid_submission_date")
            or normalized.get("bidSubmissionDate")
            or normalized.get("tender_issue_date")
            or normalized.get("tenderIssueDate")
        )
        if sub_date is not None and str(sub_date).strip() != "":
            normalized["submission_date"] = sub_date

        gst = (
            normalized.get("gst_rate")
            if normalized.get("gst_rate") is not None
            else normalized.get("gstRate")
            if normalized.get("gstRate") is not None
            else normalized.get("gst_pct")
            if normalized.get("gst_pct") is not None
            else normalized.get("gstPct")
        )
        if gst is not None and str(gst).strip() != "":
            try:
                clean_gst = re.sub(r"[^\d.]", "", str(gst))
                normalized["gst_rate"] = str(Decimal(clean_gst)) if clean_gst else str(gst).strip()
            except Exception:
                normalized["gst_rate"] = str(gst).strip()

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
    submission_date = fields.Date(allow_none=True)
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
    remarks = fields.Raw(allow_none=True)
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


class LatestBidSubmissionQuerySchema(Schema):
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
            if normalized.get("projectId") is not None
            else normalized.get("product_id")
        )
        if resolved_id is not None and str(resolved_id).strip() != "":
            normalized["project_id"] = str(resolved_id).strip()
        return normalized


class LatestBidSubmissionItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    description = fields.String(required=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)


class LatestBidSubmissionResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    gst_rate = fields.Decimal(as_string=True, places=2, allow_none=True)
    delivery_term = fields.String(allow_none=True)
    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    items = fields.List(
        fields.Nested(LatestBidSubmissionItemResponseSchema),
        required=True,
    )
