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


def _clean_email(val: str | None) -> str | None:
    if not val:
        return None
    s = str(val).strip()
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", s)
    if match:
        return match.group(0)
    return s


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


class PurchaseOrderItemCreateSchema(Schema):
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
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    net_amount = fields.Decimal(
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
        elif "description" in normalized and not normalized.get("material_name"):
            normalized["material_name"] = normalized["description"]

        if "hsn_sac" in normalized and not normalized.get("hsn_code"):
            normalized["hsn_code"] = normalized["hsn_sac"]
        elif "hsn_code" in normalized and not normalized.get("hsn_sac"):
            normalized["hsn_sac"] = normalized["hsn_code"]

        if "quantity" in normalized and normalized["quantity"] is not None:
            normalized["quantity"] = str(normalized["quantity"]).strip()
        if "unit_price" in normalized and normalized["unit_price"] is not None:
            normalized["unit_price"] = str(normalized["unit_price"]).strip()
        if "net_amount" in normalized and normalized["net_amount"] is not None:
            normalized["net_amount"] = str(normalized["net_amount"]).strip()

        return normalized


class PurchaseOrderItemUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=False, allow_none=True)
    material_name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    description = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=500),
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
        allow_none=True,
        as_string=True,
        places=3,
        validate=validate.Range(min=Decimal("0.001")),
    )
    unit_price = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        places=2,
    )
    net_amount = fields.Decimal(
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
        elif "description" in normalized and not normalized.get("material_name"):
            normalized["material_name"] = normalized["description"]

        if "hsn_sac" in normalized and not normalized.get("hsn_code"):
            normalized["hsn_code"] = normalized["hsn_sac"]
        elif "hsn_code" in normalized and not normalized.get("hsn_sac"):
            normalized["hsn_sac"] = normalized["hsn_code"]

        if "quantity" in normalized and normalized["quantity"] is not None:
            normalized["quantity"] = str(normalized["quantity"]).strip()
        if "unit_price" in normalized and normalized["unit_price"] is not None:
            normalized["unit_price"] = str(normalized["unit_price"]).strip()
        if "net_amount" in normalized and normalized["net_amount"] is not None:
            normalized["net_amount"] = str(normalized["net_amount"]).strip()

        return normalized


class PurchaseOrderCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
    )
    customer_id = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
    )
    tender_id = fields.Integer(
        required=False,
        allow_none=True,
    )
    poc_name = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    email = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    contact = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=30),
    )
    po_no = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    po_number = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    po_title = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=255),
            _not_blank,
        ),
    )
    po_date = fields.Raw(
        required=True,
    )
    delivery_date = fields.Raw(
        required=False,
        allow_none=True,
    )
    delivery_term = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    payment_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    payment_term = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
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
    gst = fields.Decimal(
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
    remark = fields.String(
        required=False,
        allow_none=True,
    )
    remarks = fields.String(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(PurchaseOrderItemCreateSchema),
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

        # tender_id
        resolved_tid = (
            normalized.get("tender_id")
            if normalized.get("tender_id") is not None
            else normalized.get("tenderId")
        )
        if resolved_tid is not None and str(resolved_tid).strip() != "":
            normalized["tender_id"] = resolved_tid

        # po_no / po_number
        resolved_po_no = (
            normalized.get("po_no")
            if normalized.get("po_no") is not None
            else normalized.get("poNo")
            if normalized.get("poNo") is not None
            else normalized.get("po_number")
            if normalized.get("po_number") is not None
            else normalized.get("poNumber")
        )
        if resolved_po_no is not None:
            normalized["po_no"] = str(resolved_po_no).strip()
            normalized["po_number"] = str(resolved_po_no).strip()

        # po_title / poTitle
        if "poTitle" in normalized and not normalized.get("po_title"):
            normalized["po_title"] = normalized["poTitle"]

        # poc_name / pocName
        if "pocName" in normalized and not normalized.get("poc_name"):
            normalized["poc_name"] = normalized["pocName"]

        # email
        if "email" in normalized and normalized["email"] is not None:
            normalized["email"] = _clean_email(normalized["email"])

        # po_date / poDate
        if "poDate" in normalized and not normalized.get("po_date"):
            normalized["po_date"] = normalized["poDate"]

        # delivery_date / deliveryDate
        if "deliveryDate" in normalized and not normalized.get("delivery_date"):
            normalized["delivery_date"] = normalized["deliveryDate"]

        # delivery_term / delivery_terms / deliveryTerm / deliveryTerms
        resolved_del_term = (
            normalized.get("delivery_term")
            if normalized.get("delivery_term") is not None
            else normalized.get("delivery_terms")
            if normalized.get("delivery_terms") is not None
            else normalized.get("deliveryTerm")
            if normalized.get("deliveryTerm") is not None
            else normalized.get("deliveryTerms")
        )
        if resolved_del_term is not None:
            normalized["delivery_term"] = resolved_del_term
            normalized["delivery_terms"] = resolved_del_term

        # payment_terms / payment_term / paymentTerms / paymentTerm
        resolved_pay_term = (
            normalized.get("payment_terms")
            if normalized.get("payment_terms") is not None
            else normalized.get("payment_term")
            if normalized.get("payment_term") is not None
            else normalized.get("paymentTerms")
            if normalized.get("paymentTerms") is not None
            else normalized.get("paymentTerm")
        )
        if resolved_pay_term is not None:
            normalized["payment_terms"] = resolved_pay_term
            normalized["payment_term"] = resolved_pay_term

        # warranty_period / warrantyPeriod
        if "warrantyPeriod" in normalized and not normalized.get("warranty_period"):
            normalized["warranty_period"] = normalized["warrantyPeriod"]

        # gst_rate / gst / gstRate
        resolved_gst = (
            normalized.get("gst_rate")
            if normalized.get("gst_rate") is not None
            else normalized.get("gstRate")
            if normalized.get("gstRate") is not None
            else normalized.get("gst")
        )
        if resolved_gst is not None:
            normalized["gst_rate"] = str(resolved_gst).strip()
            normalized["gst"] = str(resolved_gst).strip()

        # gst_amount / gstAmount
        resolved_gst_amt = (
            normalized.get("gst_amount")
            if normalized.get("gst_amount") is not None
            else normalized.get("gstAmount")
        )
        if resolved_gst_amt is not None:
            normalized["gst_amount"] = str(resolved_gst_amt).strip()

        # total_net_amount / totalNetAmount
        resolved_net_tot = (
            normalized.get("total_net_amount")
            if normalized.get("total_net_amount") is not None
            else normalized.get("totalNetAmount")
        )
        if resolved_net_tot is not None:
            normalized["total_net_amount"] = str(resolved_net_tot).strip()

        # total_gross_amount / totalGrossAmount
        resolved_gross_tot = (
            normalized.get("total_gross_amount")
            if normalized.get("total_gross_amount") is not None
            else normalized.get("totalGrossAmount")
        )
        if resolved_gross_tot is not None:
            normalized["total_gross_amount"] = str(resolved_gross_tot).strip()

        # remark / remarks
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class PurchaseOrderUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)
    customer_id = fields.Integer(required=False, allow_none=True)
    tender_id = fields.Integer(required=False, allow_none=True)
    poc_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    email = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    contact = fields.String(required=False, allow_none=True, validate=validate.Length(max=30))
    po_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    po_number = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    po_title = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    po_date = fields.Raw(required=False, allow_none=True)
    delivery_date = fields.Raw(required=False, allow_none=True)
    delivery_term = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    payment_term = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    gst_rate = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    gst_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_gross_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    remark = fields.String(required=False, allow_none=True)
    remarks = fields.String(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(PurchaseOrderItemUpdateSchema),
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
        if "tenderId" in normalized and "tender_id" not in normalized:
            normalized["tender_id"] = normalized["tenderId"]

        resolved_po_no = (
            normalized.get("po_no")
            if normalized.get("po_no") is not None
            else normalized.get("poNo")
            if normalized.get("poNo") is not None
            else normalized.get("po_number")
            if normalized.get("po_number") is not None
            else normalized.get("poNumber")
        )
        if resolved_po_no is not None:
            normalized["po_no"] = str(resolved_po_no).strip()
            normalized["po_number"] = str(resolved_po_no).strip()

        if "poTitle" in normalized and not normalized.get("po_title"):
            normalized["po_title"] = normalized["poTitle"]
        if "pocName" in normalized and not normalized.get("poc_name"):
            normalized["poc_name"] = normalized["pocName"]
        if "email" in normalized and normalized["email"] is not None:
            normalized["email"] = _clean_email(normalized["email"])
        if "poDate" in normalized and not normalized.get("po_date"):
            normalized["po_date"] = normalized["poDate"]
        if "deliveryDate" in normalized and not normalized.get("delivery_date"):
            normalized["delivery_date"] = normalized["deliveryDate"]

        if "deliveryTerms" in normalized and not normalized.get("delivery_term"):
            normalized["delivery_term"] = normalized["deliveryTerms"]
        elif "delivery_terms" in normalized and not normalized.get("delivery_term"):
            normalized["delivery_term"] = normalized["delivery_terms"]
        if "delivery_term" in normalized and not normalized.get("delivery_terms"):
            normalized["delivery_terms"] = normalized["delivery_term"]

        if "paymentTerm" in normalized and not normalized.get("payment_terms"):
            normalized["payment_terms"] = normalized["paymentTerm"]
        elif "payment_term" in normalized and not normalized.get("payment_terms"):
            normalized["payment_terms"] = normalized["payment_term"]
        if "payment_terms" in normalized and not normalized.get("payment_term"):
            normalized["payment_term"] = normalized["payment_terms"]

        if "warrantyPeriod" in normalized and not normalized.get("warranty_period"):
            normalized["warranty_period"] = normalized["warrantyPeriod"]

        resolved_gst = (
            normalized.get("gst_rate")
            if normalized.get("gst_rate") is not None
            else normalized.get("gstRate")
            if normalized.get("gstRate") is not None
            else normalized.get("gst")
        )
        if resolved_gst is not None:
            normalized["gst_rate"] = str(resolved_gst).strip()
            normalized["gst"] = str(resolved_gst).strip()

        resolved_gst_amt = (
            normalized.get("gst_amount")
            if normalized.get("gst_amount") is not None
            else normalized.get("gstAmount")
        )
        if resolved_gst_amt is not None:
            normalized["gst_amount"] = str(resolved_gst_amt).strip()

        resolved_net_tot = (
            normalized.get("total_net_amount")
            if normalized.get("total_net_amount") is not None
            else normalized.get("totalNetAmount")
        )
        if resolved_net_tot is not None:
            normalized["total_net_amount"] = str(resolved_net_tot).strip()

        resolved_gross_tot = (
            normalized.get("total_gross_amount")
            if normalized.get("total_gross_amount") is not None
            else normalized.get("totalGrossAmount")
        )
        if resolved_gross_tot is not None:
            normalized["total_gross_amount"] = str(resolved_gross_tot).strip()

        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class PurchaseOrderQuerySchema(Schema):
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
        resolved_pid = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("projectId")
        )
        if resolved_pid is not None and str(resolved_pid).strip() != "":
            normalized["project_id"] = str(resolved_pid).strip()

        resolved_cid = (
            normalized.get("customer_id")
            if normalized.get("customer_id") is not None
            else normalized.get("customerId")
        )
        if resolved_cid is not None and str(resolved_cid).strip() != "":
            normalized["customer_id"] = str(resolved_cid).strip()

        resolved_po_no = (
            normalized.get("po_no")
            if normalized.get("po_no") is not None
            else normalized.get("poNo")
            if normalized.get("poNo") is not None
            else normalized.get("po_number")
            if normalized.get("po_number") is not None
            else normalized.get("poNumber")
        )
        if resolved_po_no is not None and str(resolved_po_no).strip() != "":
            normalized["po_number"] = str(resolved_po_no).strip()
            normalized["po_no"] = str(resolved_po_no).strip()

        return normalized


class PurchaseOrderItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    purchase_order_id = fields.Integer(required=True)
    material_name = fields.String(allow_none=True)
    description = fields.String(required=True)
    hsn_code = fields.String(allow_none=True)
    hsn_sac = fields.String(allow_none=True, dump_only=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    created_at = fields.DateTime(required=True)


class PurchaseOrderResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    customer_id = fields.Integer(required=True)
    tender_id = fields.Integer(allow_none=True)
    poc_name = fields.String(allow_none=True)
    email = fields.String(allow_none=True)
    contact = fields.String(allow_none=True)
    po_no = fields.String(dump_only=True)
    po_number = fields.String(required=True)
    po_title = fields.String(required=True)
    po_date = fields.Date(required=True)
    delivery_date = fields.Date(allow_none=True)
    delivery_term = fields.String(allow_none=True)
    delivery_terms = fields.String(allow_none=True, dump_only=True)
    payment_terms = fields.String(allow_none=True)
    payment_term = fields.String(allow_none=True, dump_only=True)
    warranty_period = fields.String(allow_none=True)
    gst_rate = fields.Decimal(as_string=True, places=2, allow_none=True)
    gst = fields.Decimal(as_string=True, places=2, allow_none=True, dump_only=True)
    gst_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_gross_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    remark = fields.String(allow_none=True)
    remarks = fields.String(allow_none=True, dump_only=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(PurchaseOrderItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=False,
    )


class LatestPurchaseOrderItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    material_name = fields.String(allow_none=True)
    hsn_code = fields.String(allow_none=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, allow_none=True)
    net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)


class LatestPurchaseOrderResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    po_number = fields.String(allow_none=True)
    po_date = fields.Date(allow_none=True)
    gst_rate = fields.Decimal(as_string=True, places=2, allow_none=True)
    gst_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    items = fields.List(
        fields.Nested(LatestPurchaseOrderItemResponseSchema),
        required=True,
    )


