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


class SupplierOrderConfirmationItemCreateSchema(Schema):
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

        # description / material_name
        desc = (
            normalized.get("description")
            or normalized.get("material_name")
            or normalized.get("item_name")
            or normalized.get("material_description")
        )
        if desc is None or not str(desc).strip():
            sr_no = normalized.get("sr_no") or 1
            desc = f"Order Item {sr_no}"
        normalized["description"] = str(desc).strip()
        if not normalized.get("material_name"):
            normalized["material_name"] = normalized["description"]

        # hsn_code / hsn_sac
        hsn = (
            normalized.get("hsn_code")
            if normalized.get("hsn_code") is not None
            else normalized.get("hsn_sac")
            if normalized.get("hsn_sac") is not None
            else normalized.get("hsn")
        )
        if hsn is not None and str(hsn).strip():
            normalized["hsn_code"] = str(hsn).strip()
            normalized["hsn_sac"] = str(hsn).strip()
        else:
            normalized["hsn_code"] = None
            normalized["hsn_sac"] = None

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
            normalized["unit_price"] = "0.00"
        else:
            try:
                clean_p = re.sub(r"[^\d.]", "", str(uprice))
                normalized["unit_price"] = str(Decimal(clean_p)) if clean_p else "0.00"
            except Exception:
                normalized["unit_price"] = "0.00"

        # net_amount / total_amount
        total = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netAmount")
            if normalized.get("netAmount") is not None
            else normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("totalAmount")
            if normalized.get("totalAmount") is not None
            else normalized.get("net_total")
            if normalized.get("net_total") is not None
            else normalized.get("total")
        )
        if total is not None and str(total).strip() != "":
            try:
                clean_t = re.sub(r"[^\d.]", "", str(total))
                normalized["net_amount"] = str(Decimal(clean_t)) if clean_t else None
            except Exception:
                normalized["net_amount"] = None
        else:
            try:
                d_qty = Decimal(normalized["quantity"])
                d_price = Decimal(normalized["unit_price"])
                normalized["net_amount"] = str((d_qty * d_price).quantize(Decimal("0.01")))
            except Exception:
                normalized["net_amount"] = None

        return normalized


class SupplierOrderConfirmationItemUpdateSchema(Schema):
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

        if "material_name" in normalized or "description" in normalized:
            desc = normalized.get("description") or normalized.get("material_name")
            if desc is not None and str(desc).strip():
                normalized["description"] = str(desc).strip()
                normalized["material_name"] = str(desc).strip()
            else:
                normalized["description"] = None
                normalized["material_name"] = None

        if "hsn_sac" in normalized or "hsn_code" in normalized or "hsn" in normalized:
            hsn = normalized.get("hsn_code") or normalized.get("hsn_sac") or normalized.get("hsn")
            if hsn is not None and str(hsn).strip():
                normalized["hsn_code"] = str(hsn).strip()
                normalized["hsn_sac"] = str(hsn).strip()
            else:
                normalized["hsn_code"] = None
                normalized["hsn_sac"] = None

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
                    normalized["unit_price"] = str(Decimal(clean_p)) if clean_p else "0.00"
                except Exception:
                    normalized["unit_price"] = "0.00"

        total = (
            normalized.get("net_amount")
            if normalized.get("net_amount") is not None
            else normalized.get("netAmount")
            if normalized.get("netAmount") is not None
            else normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("totalAmount")
            if normalized.get("totalAmount") is not None
            else normalized.get("net_total")
            if normalized.get("net_total") is not None
            else normalized.get("total")
        )
        if total is not None:
            if str(total).strip() == "":
                normalized["net_amount"] = None
            else:
                try:
                    clean_t = re.sub(r"[^\d.]", "", str(total))
                    normalized["net_amount"] = str(Decimal(clean_t)) if clean_t else None
                except Exception:
                    normalized["net_amount"] = None
        return normalized


class SupplierOrderConfirmationCreateSchema(Schema):
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
    purchase_order_id = fields.Integer(
        required=False,
        allow_none=True,
    )
    order_confirmation_date = fields.Raw(
        required=True,
    )
    confirmation_date = fields.Raw(
        required=False,
        allow_none=True,
    )
    ref_no = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=100),
            _not_blank,
        ),
    )
    reference_number = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    email = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=255),
    )
    shipping_terms = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    shipping_term = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_period = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=100),
    )
    delivery_term = fields.String(
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
    total_amount = fields.Decimal(
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
    currency_unit = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=20),
    )
    remark = fields.Raw(
        required=False,
        allow_none=True,
    )
    remarks = fields.Raw(
        required=False,
        allow_none=True,
    )
    items = fields.List(
        fields.Nested(SupplierOrderConfirmationItemCreateSchema),
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

        # supplier_id
        resolved_sid = (
            normalized.get("supplier_id")
            if normalized.get("supplier_id") is not None
            else normalized.get("supplierId")
        )
        if resolved_sid is not None and str(resolved_sid).strip() != "":
            normalized["supplier_id"] = resolved_sid

        # purchase_order_id
        resolved_poid = (
            normalized.get("purchase_order_id")
            if normalized.get("purchase_order_id") is not None
            else normalized.get("purchaseOrderId")
            if normalized.get("purchaseOrderId") is not None
            else normalized.get("po_id")
            if normalized.get("po_id") is not None
            else normalized.get("poId")
        )
        if resolved_poid is not None and str(resolved_poid).strip() != "":
            normalized["purchase_order_id"] = resolved_poid

        # order_confirmation_date / confirmation_date
        resolved_date = (
            normalized.get("order_confirmation_date")
            if normalized.get("order_confirmation_date") is not None
            else normalized.get("orderConfirmationDate")
            if normalized.get("orderConfirmationDate") is not None
            else normalized.get("confirmation_date")
            if normalized.get("confirmation_date") is not None
            else normalized.get("confirmationDate")
        )
        if resolved_date is not None:
            normalized["order_confirmation_date"] = resolved_date
            normalized["confirmation_date"] = resolved_date

        # ref_no / reference_number / order_confirmation_no / confirmation_no
        resolved_ref = (
            normalized.get("ref_no")
            if normalized.get("ref_no") is not None
            else normalized.get("refNo")
            if normalized.get("refNo") is not None
            else normalized.get("order_confirmation_no")
            if normalized.get("order_confirmation_no") is not None
            else normalized.get("orderConfirmationNo")
            if normalized.get("orderConfirmationNo") is not None
            else normalized.get("order_confirmation_number")
            if normalized.get("order_confirmation_number") is not None
            else normalized.get("orderConfirmationNumber")
            if normalized.get("orderConfirmationNumber") is not None
            else normalized.get("reference_number")
            if normalized.get("reference_number") is not None
            else normalized.get("referenceNumber")
            if normalized.get("referenceNumber") is not None
            else normalized.get("confirmation_no")
            if normalized.get("confirmation_no") is not None
            else normalized.get("confirmation_number")
            if normalized.get("confirmation_number") is not None
            else normalized.get("oc_no")
            if normalized.get("oc_no") is not None
            else normalized.get("oc_number")
        )
        if resolved_ref is not None and str(resolved_ref).strip() != "":
            normalized["ref_no"] = str(resolved_ref).strip()
            normalized["reference_number"] = str(resolved_ref).strip()
        elif not normalized.get("ref_no"):
            normalized["ref_no"] = f"OC-{normalized.get('project_id') or 1}"
            normalized["reference_number"] = normalized["ref_no"]

        # email
        if "email" in normalized and normalized["email"] is not None:
            normalized["email"] = _clean_email(normalized["email"])

        # shipping_terms / shipping_term / incoterms / inco_terms
        resolved_shipping = (
            normalized.get("shipping_terms")
            if normalized.get("shipping_terms") is not None
            else normalized.get("shipping_term")
            if normalized.get("shipping_term") is not None
            else normalized.get("incoterms")
            if normalized.get("incoterms") is not None
            else normalized.get("inco_terms")
            if normalized.get("inco_terms") is not None
            else normalized.get("shippingTerms")
            if normalized.get("shippingTerms") is not None
            else normalized.get("shippingTerm")
        )
        if resolved_shipping is not None:
            normalized["shipping_terms"] = str(resolved_shipping).strip()
            normalized["shipping_term"] = str(resolved_shipping).strip()

        # delivery_period / delivery_term
        resolved_delivery = (
            normalized.get("delivery_period")
            if normalized.get("delivery_period") is not None
            else normalized.get("delivery_term")
            if normalized.get("delivery_term") is not None
            else normalized.get("deliveryPeriod")
            if normalized.get("deliveryPeriod") is not None
            else normalized.get("deliveryTerm")
        )
        if resolved_delivery is not None:
            normalized["delivery_period"] = str(resolved_delivery).strip()
            normalized["delivery_term"] = str(resolved_delivery).strip()

        # payment_terms / payment_term
        resolved_payment = (
            normalized.get("payment_terms")
            if normalized.get("payment_terms") is not None
            else normalized.get("payment_term")
            if normalized.get("payment_term") is not None
            else normalized.get("paymentTerms")
            if normalized.get("paymentTerms") is not None
            else normalized.get("paymentTerm")
        )
        if resolved_payment is not None:
            normalized["payment_terms"] = str(resolved_payment).strip()
            normalized["payment_term"] = str(resolved_payment).strip()

        # warranty_period
        if "warrantyPeriod" in normalized and not normalized.get("warranty_period"):
            normalized["warranty_period"] = normalized["warrantyPeriod"]

        # total_amount / totalAmount
        resolved_total = (
            normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("totalAmount")
        )
        if resolved_total is not None and str(resolved_total).strip() != "":
            normalized["total_amount"] = str(resolved_total).strip()

        # total_net_amount / totalNetAmount
        resolved_net_total = (
            normalized.get("total_net_amount")
            if normalized.get("total_net_amount") is not None
            else normalized.get("totalNetAmount")
        )
        if resolved_net_total is not None and str(resolved_net_total).strip() != "":
            normalized["total_net_amount"] = str(resolved_net_total).strip()

        # Root total_amount calculation fallback from items
        if not normalized.get("total_amount") and normalized.get("items"):
            try:
                calc_total = sum(
                    Decimal(str(it.get("net_amount") or it.get("total_amount") or 0))
                    for it in normalized["items"]
                    if isinstance(it, (dict, Mapping))
                )
                if calc_total > 0:
                    normalized["total_amount"] = str(calc_total)
                    if not normalized.get("total_net_amount"):
                        normalized["total_net_amount"] = str(calc_total)
            except Exception:
                pass

        # currency_unit / currencyUnit / currency
        resolved_curr = (
            normalized.get("currency_unit")
            if normalized.get("currency_unit") is not None
            else normalized.get("currencyUnit")
            if normalized.get("currencyUnit") is not None
            else normalized.get("currency")
        )
        if resolved_curr is not None:
            normalized["currency_unit"] = str(resolved_curr).strip().upper()

        # remark / remarks
        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        # clean items
        if "items" in normalized and isinstance(normalized["items"], list):
            normalized["items"] = [
                item for item in normalized["items"] if isinstance(item, (dict, Mapping))
            ]

        return normalized


class SupplierOrderConfirmationUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(required=False, allow_none=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    purchase_order_id = fields.Integer(required=False, allow_none=True)
    order_confirmation_date = fields.Raw(required=False, allow_none=True)
    confirmation_date = fields.Raw(required=False, allow_none=True)
    ref_no = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    reference_number = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    email = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    shipping_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    shipping_term = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    delivery_term = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    payment_terms = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    payment_term = fields.String(required=False, allow_none=True, validate=validate.Length(max=255))
    warranty_period = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    total_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    total_net_amount = fields.Decimal(required=False, allow_none=True, as_string=True, places=2)
    currency_unit = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    remark = fields.Raw(required=False, allow_none=True)
    remarks = fields.Raw(required=False, allow_none=True)
    items = fields.List(
        fields.Nested(SupplierOrderConfirmationItemUpdateSchema),
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
        if "supplierId" in normalized and "supplier_id" not in normalized:
            normalized["supplier_id"] = normalized["supplierId"]
        if "purchaseOrderId" in normalized and "purchase_order_id" not in normalized:
            normalized["purchase_order_id"] = normalized["purchaseOrderId"]

        resolved_date = (
            normalized.get("order_confirmation_date")
            if normalized.get("order_confirmation_date") is not None
            else normalized.get("orderConfirmationDate")
            if normalized.get("orderConfirmationDate") is not None
            else normalized.get("confirmation_date")
            if normalized.get("confirmation_date") is not None
            else normalized.get("confirmationDate")
        )
        if resolved_date is not None:
            normalized["order_confirmation_date"] = resolved_date
            normalized["confirmation_date"] = resolved_date

        resolved_ref = (
            normalized.get("ref_no")
            if normalized.get("ref_no") is not None
            else normalized.get("refNo")
            if normalized.get("refNo") is not None
            else normalized.get("order_confirmation_no")
            if normalized.get("order_confirmation_no") is not None
            else normalized.get("orderConfirmationNo")
            if normalized.get("orderConfirmationNo") is not None
            else normalized.get("order_confirmation_number")
            if normalized.get("order_confirmation_number") is not None
            else normalized.get("orderConfirmationNumber")
            if normalized.get("orderConfirmationNumber") is not None
            else normalized.get("reference_number")
            if normalized.get("reference_number") is not None
            else normalized.get("referenceNumber")
            if normalized.get("referenceNumber") is not None
            else normalized.get("confirmation_no")
            if normalized.get("confirmation_no") is not None
            else normalized.get("confirmation_number")
        )
        if resolved_ref is not None and str(resolved_ref).strip() != "":
            normalized["ref_no"] = str(resolved_ref).strip()
            normalized["reference_number"] = str(resolved_ref).strip()

        if "email" in normalized and normalized["email"] is not None:
            normalized["email"] = _clean_email(normalized["email"])

        resolved_shipping = (
            normalized.get("shipping_terms")
            if normalized.get("shipping_terms") is not None
            else normalized.get("shipping_term")
            if normalized.get("shipping_term") is not None
            else normalized.get("incoterms")
            if normalized.get("incoterms") is not None
            else normalized.get("inco_terms")
            if normalized.get("inco_terms") is not None
            else normalized.get("shippingTerms")
            if normalized.get("shippingTerms") is not None
            else normalized.get("shippingTerm")
        )
        if resolved_shipping is not None:
            normalized["shipping_terms"] = str(resolved_shipping).strip()
            normalized["shipping_term"] = str(resolved_shipping).strip()

        resolved_delivery = (
            normalized.get("delivery_period")
            if normalized.get("delivery_period") is not None
            else normalized.get("delivery_term")
            if normalized.get("delivery_term") is not None
            else normalized.get("deliveryPeriod")
            if normalized.get("deliveryPeriod") is not None
            else normalized.get("deliveryTerm")
        )
        if resolved_delivery is not None:
            normalized["delivery_period"] = str(resolved_delivery).strip()
            normalized["delivery_term"] = str(resolved_delivery).strip()

        resolved_payment = (
            normalized.get("payment_terms")
            if normalized.get("payment_terms") is not None
            else normalized.get("payment_term")
            if normalized.get("payment_term") is not None
            else normalized.get("paymentTerms")
            if normalized.get("paymentTerms") is not None
            else normalized.get("paymentTerm")
        )
        if resolved_payment is not None:
            normalized["payment_terms"] = str(resolved_payment).strip()
            normalized["payment_term"] = str(resolved_payment).strip()

        if "warrantyPeriod" in normalized and not normalized.get("warranty_period"):
            normalized["warranty_period"] = normalized["warrantyPeriod"]

        resolved_total = (
            normalized.get("total_amount")
            if normalized.get("total_amount") is not None
            else normalized.get("totalAmount")
        )
        if resolved_total is not None and str(resolved_total).strip() != "":
            normalized["total_amount"] = str(resolved_total).strip()

        resolved_net_total = (
            normalized.get("total_net_amount")
            if normalized.get("total_net_amount") is not None
            else normalized.get("totalNetAmount")
        )
        if resolved_net_total is not None and str(resolved_net_total).strip() != "":
            normalized["total_net_amount"] = str(resolved_net_total).strip()

        if "currency_unit" in normalized or "currencyUnit" in normalized or "currency" in normalized:
            resolved_curr = (
                normalized.get("currency_unit")
                if normalized.get("currency_unit") is not None
                else normalized.get("currencyUnit")
                if normalized.get("currencyUnit") is not None
                else normalized.get("currency")
            )
            if resolved_curr is not None:
                normalized["currency_unit"] = str(resolved_curr).strip().upper()

        if "remarks" in normalized and not normalized.get("remark"):
            normalized["remark"] = normalized["remarks"]
        elif "remark" in normalized and not normalized.get("remarks"):
            normalized["remarks"] = normalized["remark"]

        return normalized


class SupplierOrderConfirmationQuerySchema(Schema):
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

        resolved_ref = (
            normalized.get("ref_no")
            if normalized.get("ref_no") is not None
            else normalized.get("refNo")
            if normalized.get("refNo") is not None
            else normalized.get("reference_number")
            if normalized.get("reference_number") is not None
            else normalized.get("referenceNumber")
        )
        if resolved_ref is not None and str(resolved_ref).strip() != "":
            normalized["ref_no"] = str(resolved_ref).strip()
            normalized["reference_number"] = str(resolved_ref).strip()

        return normalized


class SupplierOrderConfirmationItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    supplier_order_confirmation_id = fields.Integer(required=True)
    material_name = fields.String(allow_none=True)
    description = fields.String(required=True)
    item_description = fields.String(dump_only=True)
    hsn_code = fields.String(allow_none=True)
    hsn_sac = fields.String(dump_only=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    unit_price = fields.Decimal(as_string=True, places=2, required=True)
    net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_amount = fields.Decimal(attribute="net_amount", as_string=True, places=2, allow_none=True, dump_only=True)
    created_at = fields.DateTime(required=True)


class SupplierOrderConfirmationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    supplier_id = fields.Integer(required=False, allow_none=True)
    purchase_order_id = fields.Integer(allow_none=True)
    order_confirmation_date = fields.Date(required=True)
    confirmation_date = fields.Date(dump_only=True)
    email = fields.String(allow_none=True)
    ref_no = fields.String(required=False, allow_none=True)
    reference_number = fields.String(dump_only=True)
    order_confirmation_no = fields.String(attribute="ref_no", dump_only=True)
    order_confirmation_number = fields.String(attribute="ref_no", dump_only=True)
    shipping_terms = fields.String(allow_none=True)
    shipping_term = fields.String(dump_only=True)
    incoterms = fields.String(attribute="shipping_terms", dump_only=True)
    delivery_period = fields.String(allow_none=True)
    delivery_term = fields.String(dump_only=True)
    payment_terms = fields.String(allow_none=True)
    payment_term = fields.String(dump_only=True)
    warranty_period = fields.String(allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    total_net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    currency_unit = fields.String(allow_none=True)
    remarks = fields.Raw(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
    items = fields.List(
        fields.Nested(SupplierOrderConfirmationItemResponseSchema),
        required=True,
    )
    attachments = fields.List(
        fields.Nested(AttachmentResponseSchema),
        required=False,
    )


class LatestSupplierOrderConfirmationQuerySchema(Schema):
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


class LatestSupplierOrderConfirmationItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    unit_price = fields.Decimal(as_string=True, places=2, required=True)
    quantity = fields.Decimal(as_string=True, places=3, required=True)
    material_name = fields.String(allow_none=True)
    hsn_code = fields.String(allow_none=True)
    net_amount = fields.Decimal(as_string=True, places=2, allow_none=True)


class LatestSupplierOrderConfirmationResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    payment_terms = fields.String(allow_none=True)
    warranty_period = fields.String(allow_none=True)
    shipping_terms = fields.String(allow_none=True)
    delivery_period = fields.String(allow_none=True)
    total_amount = fields.Decimal(as_string=True, places=2, allow_none=True)
    currency_unit = fields.String(allow_none=True)
    items = fields.List(
        fields.Nested(LatestSupplierOrderConfirmationItemResponseSchema),
        required=True,
    )
