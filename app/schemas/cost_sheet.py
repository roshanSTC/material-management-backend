from math import isfinite

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
    pre_load,
    validate,
    validates_schema,
)


def _finite(value: float) -> None:
    if not isfinite(value):
        raise ValidationError("Value must be a finite number.")


def _not_blank(value: str) -> None:
    if not value or not str(value).strip():
        raise ValidationError("Field must not be blank.")


def _normalize_rate(val):
    if val is None:
        return None
    try:
        num = float(val)
    except (ValueError, TypeError):
        return val
    if num >= 1.0:
        return num / 100.0
    return num


RATE_VALIDATOR = validate.And(validate.Range(min=0, max=1), _finite)
POSITIVE_VALUE_VALIDATOR = validate.And(validate.Range(min=0.000001), _finite)
NON_BLANK_SHORT_TEXT = validate.And(validate.Length(min=1, max=100), _not_blank)


class CostSheetGlobalParamsSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    eurToInr = fields.Float(required=True, validate=POSITIVE_VALUE_VALIDATOR)
    insuranceFreightRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    defaultCustomsDutyRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    igstRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    transportationRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    financeChargesRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    marginRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    gstRate = fields.Float(required=True, validate=RATE_VALIDATOR)

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        mapping = {
            "eur_to_inr": "eurToInr",
            "insurance_freight_rate": "insuranceFreightRate",
            "default_customs_duty_rate": "defaultCustomsDutyRate",
            "igst_rate": "igstRate",
            "transportation_rate": "transportationRate",
            "finance_charges_rate": "financeChargesRate",
            "margin_rate": "marginRate",
            "gst_rate": "gstRate",
        }
        normalized = dict(data)
        for snake_key, camel_key in mapping.items():
            if snake_key in normalized:
                val = normalized.pop(snake_key)
                if camel_key not in normalized:
                    normalized[camel_key] = val

        for rate_key in (
            "insuranceFreightRate",
            "defaultCustomsDutyRate",
            "igstRate",
            "transportationRate",
            "financeChargesRate",
            "marginRate",
            "gstRate",
        ):
            if rate_key in normalized:
                normalized[rate_key] = _normalize_rate(normalized[rate_key])

        return normalized


class CostSheetItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    quotationNumber = fields.String(required=False, allow_none=True)
    quotationIndex = fields.String(required=False, allow_none=True)
    itemDescription = fields.String(
        required=True,
        validate=validate.And(validate.Length(min=1, max=500), _not_blank),
    )
    itemCode = fields.String(required=True, validate=NON_BLANK_SHORT_TEXT)
    pricePerUnitEur = fields.Float(required=True, validate=POSITIVE_VALUE_VALIDATOR)
    quantity = fields.Float(required=True, validate=POSITIVE_VALUE_VALIDATOR)
    customsDutyRate = fields.Float(
        required=False,
        allow_none=True,
        validate=RATE_VALIDATOR,
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        mapping = {
            "quotation_number": "quotationNumber",
            "quotation_index": "quotationIndex",
            "item_description": "itemDescription",
            "item_code": "itemCode",
            "price_per_unit_eur": "pricePerUnitEur",
            "customs_duty_rate": "customsDutyRate",
        }
        normalized = dict(data)
        for snake_key, camel_key in mapping.items():
            if snake_key in normalized:
                val = normalized.pop(snake_key)
                if camel_key not in normalized:
                    normalized[camel_key] = val

        if "customsDutyRate" in normalized:
            normalized["customsDutyRate"] = _normalize_rate(normalized["customsDutyRate"])

        return normalized


class CostSheetRequestSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    globalParams = fields.Nested(CostSheetGlobalParamsSchema, required=True)
    items = fields.List(
        fields.Nested(CostSheetItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "global_params" in normalized:
            gp = normalized.pop("global_params")
            if "globalParams" not in normalized:
                normalized["globalParams"] = gp
        return normalized


class CostSheetCalculatedItemSchema(CostSheetItemSchema):
    totalPriceEur = fields.Float(required=True)
    insuranceFreightEur = fields.Float(required=True)
    landedCostEur = fields.Float(required=True)
    landedCostInr = fields.Float(required=True)
    customsDutyInr = fields.Float(required=True)
    igstInr = fields.Float(required=True)
    transportationInr = fields.Float(required=True)
    financingChargesInr = fields.Float(required=True)
    totalCostInr = fields.Float(required=True)
    lessIgstInr = fields.Float(required=True)
    marginInr = fields.Float(required=True)
    sellingPriceExclGst = fields.Float(required=True)
    sellingPriceInclGst = fields.Float(required=True)


class CostSheetCalculationResponseSchema(Schema):
    globalParams = fields.Nested(CostSheetGlobalParamsSchema, required=True)
    items = fields.List(fields.Nested(CostSheetCalculatedItemSchema), required=True)
    columnTotals = fields.Dict(keys=fields.String(), values=fields.Float(), required=True)
    totalSellingPriceExclGst = fields.Float(required=True)
    totalGst = fields.Float(required=True)
    grandTotalInclGst = fields.Float(required=True)


class ProjectCostSheetItemSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    quotationNumber = fields.String(
        required=False,
        allow_none=True,
    )
    quotationIndex = fields.String(
        required=False,
        allow_none=True,
    )
    itemDescription = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=500),
            _not_blank,
        ),
    )
    itemCode = fields.String(
        required=True,
        validate=NON_BLANK_SHORT_TEXT,
    )
    pricePerUnitEur = fields.Float(
        required=False,
        allow_none=True,
        validate=POSITIVE_VALUE_VALIDATOR,
    )
    pricePerUnitInr = fields.Float(
        required=False,
        allow_none=True,
        validate=POSITIVE_VALUE_VALIDATOR,
    )
    quantity = fields.Float(
        required=True,
        validate=POSITIVE_VALUE_VALIDATOR,
    )
    customsDutyRate = fields.Float(
        required=False,
        allow_none=True,
        validate=RATE_VALIDATOR,
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        mapping = {
            "quotation_number": "quotationNumber",
            "quotation_index": "quotationIndex",
            "item_description": "itemDescription",
            "item_code": "itemCode",
            "price_per_unit_eur": "pricePerUnitEur",
            "price_per_unit_inr": "pricePerUnitInr",
            "customs_duty_rate": "customsDutyRate",
        }
        normalized = dict(data)
        for snake_key, camel_key in mapping.items():
            if snake_key in normalized:
                val = normalized.pop(snake_key)
                if camel_key not in normalized:
                    normalized[camel_key] = val

        if "customsDutyRate" in normalized:
            normalized["customsDutyRate"] = _normalize_rate(normalized["customsDutyRate"])

        return normalized

    @validates_schema
    def validate_price(self, data, **kwargs):
        if data.get("pricePerUnitEur") is None and data.get("pricePerUnitInr") is None:
            raise ValidationError("Either pricePerUnitEur or pricePerUnitInr must be provided.")


class ProjectCostSheetCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        metadata={"description": "Project ID"},
    )
    title = fields.String(
        required=True,
        validate=validate.And(validate.Length(min=1, max=255), _not_blank),
    )
    globalParams = fields.Nested(CostSheetGlobalParamsSchema, required=True)
    items = fields.List(
        fields.Nested(ProjectCostSheetItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @pre_load
    def normalize_payload(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        # Normalize globalParams
        if "global_params" in normalized:
            gp = normalized.pop("global_params")
            if "globalParams" not in normalized:
                normalized["globalParams"] = gp
        # Normalize project_id / product_id aliases
        resolved_id = (
            normalized.get("project_id")
            if normalized.get("project_id") is not None
            else normalized.get("product_id")
            if normalized.get("product_id") is not None
            else normalized.get("projectId")
            if normalized.get("projectId") is not None
            else normalized.get("productId")
        )
        if resolved_id is not None:
            normalized["project_id"] = resolved_id
        return normalized

    @post_load
    def finalize_payload(self, data, **kwargs):
        resolved_id = data.get("project_id") or data.get("product_id")
        data["project_id"] = resolved_id
        data["product_id"] = resolved_id
        data.setdefault("status", "Draft")
        return data


class ProjectCostSheetQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=False,
        allow_none=True,
        metadata={"description": "Filter by Project ID"},
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, dict):
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
        if resolved_id is not None:
            normalized["project_id"] = resolved_id
        return normalized


class LatestCostSheetQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    project_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
        metadata={"description": "Project ID"},
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, dict):
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
        if resolved_id is not None:
            normalized["project_id"] = resolved_id
        return normalized


class CostSheetItemRateUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    pricePerUnitEur = fields.Float(required=True, validate=POSITIVE_VALUE_VALIDATOR)
    supplierName = fields.String(
        required=True,
        validate=validate.And(validate.Length(min=1, max=255), _not_blank),
    )
    changeReason = fields.String(
        required=True,
        validate=validate.And(validate.Length(min=1), _not_blank),
    )

    @pre_load
    def normalize_keys(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        mapping = {
            "price_per_unit_eur": "pricePerUnitEur",
            "supplier_name": "supplierName",
            "change_reason": "changeReason",
        }
        normalized = dict(data)
        for snake_key, camel_key in mapping.items():
            if snake_key in normalized:
                val = normalized.pop(snake_key)
                if camel_key not in normalized:
                    normalized[camel_key] = val
        return normalized


class ItemPriceHistoryResponseSchema(Schema):
    id = fields.Integer(required=True)
    oldPriceEur = fields.Float(required=True)
    newPriceEur = fields.Float(required=True)
    supplierName = fields.String(required=True)
    changeReason = fields.String(required=True)
    changedBy = fields.Integer(required=True)
    createdAt = fields.DateTime(required=True)
    isRateIncrease = fields.Boolean(required=True)


class ProjectCostSheetItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    quotationNumber = fields.String(required=False, allow_none=True)
    quotationIndex = fields.String(required=False, allow_none=True)
    itemCode = fields.String(required=True)
    itemDescription = fields.String(required=True)
    pricePerUnitInr = fields.Float(required=False, allow_none=True)
    quantity = fields.Float(required=True)
    totalPriceInr = fields.Float(required=False, allow_none=True)
    pricePerUnitEur = fields.Float(required=True)
    totalPriceEur = fields.Float(required=False, allow_none=True)
    customsDutyRate = fields.Float(allow_none=True)
    hasRateIncrease = fields.Boolean(required=True)
    latestPriceChange = fields.Nested(
        ItemPriceHistoryResponseSchema,
        allow_none=True,
    )
    createdAt = fields.DateTime(required=True)
    updatedAt = fields.DateTime(required=True)


class ProjectCostSheetMetadataResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    product_id = fields.Integer(required=True)
    versionNumber = fields.Integer(required=True)
    title = fields.String(required=True)
    totalPriceInr = fields.Float(required=False, allow_none=True)
    cumulativeProjectCostInr = fields.Float(required=True)
    grandTotalInclGst = fields.Float(required=False, allow_none=True)
    totalSellingPriceExclGst = fields.Float(required=False, allow_none=True)
    totalGst = fields.Float(required=False, allow_none=True)
    globalParams = fields.Nested(CostSheetGlobalParamsSchema, required=True)
    output = fields.Dict(required=False, allow_none=True)
    status = fields.String(required=True)
    createdBy = fields.Integer(required=True)
    createdAt = fields.DateTime(required=True)
    updatedAt = fields.DateTime(required=True)
    totalItemCount = fields.Integer(required=True)
    hasRateIncrease = fields.Boolean(required=True)
    latestPriceChange = fields.Nested(
        ItemPriceHistoryResponseSchema,
        allow_none=True,
    )
    recentPriceChanges = fields.List(
        fields.Nested(ItemPriceHistoryResponseSchema),
        required=True,
    )
    items = fields.List(fields.Nested(ProjectCostSheetItemResponseSchema), required=True)


class LatestCostSheetItemResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    itemCode = fields.String(required=True)
    itemDescription = fields.String(required=True)
    pricePerUnitInr = fields.Float(required=True)
    quantity = fields.Float(required=True)
    totalPriceInr = fields.Float(required=True)


class LatestCostSheetResponseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(required=True)
    project_id = fields.Integer(required=True)
    title = fields.String(required=True)
    totalPriceInr = fields.Float(required=True)
    items = fields.List(fields.Nested(LatestCostSheetItemResponseSchema), required=True)

