from math import isfinite

from marshmallow import Schema, ValidationError, fields, validate


def _finite(value: float) -> None:
    if not isfinite(value):
        raise ValidationError("Value must be a finite number.")


def _not_blank(value: str) -> None:
    if not value.strip():
        raise ValidationError("Field must not be blank.")


RATE_VALIDATOR = validate.And(validate.Range(min=0, max=1), _finite)
POSITIVE_VALUE_VALIDATOR = validate.And(validate.Range(min=0.000001), _finite)
NON_BLANK_SHORT_TEXT = validate.And(validate.Length(min=1, max=100), _not_blank)


class CostSheetGlobalParamsSchema(Schema):
    eurToInr = fields.Float(required=True, validate=POSITIVE_VALUE_VALIDATOR)
    insuranceFreightRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    defaultCustomsDutyRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    igstRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    transportationRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    financeChargesRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    marginRate = fields.Float(required=True, validate=RATE_VALIDATOR)
    gstRate = fields.Float(required=True, validate=RATE_VALIDATOR)


class CostSheetItemSchema(Schema):
    quotationNumber = fields.String(required=True, validate=NON_BLANK_SHORT_TEXT)
    quotationIndex = fields.String(required=True, validate=NON_BLANK_SHORT_TEXT)
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


class CostSheetRequestSchema(Schema):
    globalParams = fields.Nested(CostSheetGlobalParamsSchema, required=True)
    items = fields.List(
        fields.Nested(CostSheetItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )


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

    quotationNumber = fields.String(
        required=True,
        validate=NON_BLANK_SHORT_TEXT,
    )

    quotationIndex = fields.String(
        required=True,
        validate=NON_BLANK_SHORT_TEXT,
    )

    itemCode = fields.String(
        required=True,
        validate=NON_BLANK_SHORT_TEXT,
    )

    itemDescription = fields.String(
        required=True,
        validate=validate.And(
            validate.Length(min=1, max=500),
            _not_blank,
        ),
    )

    pricePerUnitEur = fields.Float(
        required=True,
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
    
    

class ProjectCostSheetCreateSchema(Schema):
    title = fields.String(
        required=True,
        validate=validate.And(validate.Length(min=1, max=255), _not_blank),
    )
    globalParams = fields.Nested(CostSheetGlobalParamsSchema, required=True)
    status = fields.String(
        load_default="Draft",
        validate=validate.OneOf(["Draft", "Approved", "Archived"]),
    )
    items = fields.List(
        fields.Nested(ProjectCostSheetItemSchema),
        required=True,
        validate=validate.Length(min=1),
    )


class CostSheetItemRateUpdateSchema(Schema):
    pricePerUnitEur = fields.Float(required=True, validate=POSITIVE_VALUE_VALIDATOR)
    supplierName = fields.String(
        required=True,
        validate=validate.And(validate.Length(min=1, max=255), _not_blank),
    )
    changeReason = fields.String(
        required=True,
        validate=validate.And(validate.Length(min=1), _not_blank),
    )


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
    id = fields.Integer(required=True)
    itemCode = fields.String(required=True)
    itemDescription = fields.String(required=True)
    pricePerUnitEur = fields.Float(required=True)
    quotationNumber = fields.String(required=True)
    quotationIndex = fields.String(required=True)
    quantity = fields.Float(required=True)
    customsDutyRate = fields.Float(allow_none=True)
    hasRateIncrease = fields.Boolean(required=True)
    latestPriceChange = fields.Nested(
        ItemPriceHistoryResponseSchema,
        allow_none=True,
    )
    createdAt = fields.DateTime(required=True)
    updatedAt = fields.DateTime(required=True)


class ProjectCostSheetMetadataResponseSchema(Schema):
    id = fields.Integer(required=True)
    projectId = fields.Integer(required=True)
    versionNumber = fields.Integer(required=True)
    title = fields.String(required=True)
    globalParams = fields.Nested(CostSheetGlobalParamsSchema, required=True)
    status = fields.String(required=True)
    createdBy = fields.Integer(required=True)
    createdAt = fields.DateTime(required=True)
    updatedAt = fields.DateTime(required=True)
    totalItemCount = fields.Integer(required=True)
    cumulativeProjectCostInr = fields.Float(required=True)
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
