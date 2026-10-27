"""Schemas and data models for AI Assistant."""

from marshmallow import Schema, fields


class QueryRequestSchema(Schema):
    """Input payload for natural language AI database queries."""

    question = fields.String(
        required=True,
        metadata={"description": "Natural language question about application data"},
    )
    history = fields.List(
        fields.Dict(),
        load_default=list,
        metadata={"description": "Optional conversation history for context"},
    )


class QueryResponseSchema(Schema):
    """Structured response containing AI answer, generated SQL, and query result."""

    success = fields.Boolean(required=True)
    type = fields.String(dump_default="table")
    question = fields.String(required=True)
    summary = fields.String(
        allow_none=True,
        metadata={"description": "Natural language summary of results"},
    )
    sql = fields.String(
        allow_none=True,
        metadata={"description": "Validated read-only SQL query executed"},
    )
    columns = fields.List(
        fields.String(),
        dump_default=list,
        metadata={"description": "Column names of the result set"},
    )
    rows = fields.List(
        fields.Dict(),
        dump_default=list,
        metadata={"description": "Rows returned from the read-only query"},
    )
    total_rows = fields.Integer(dump_default=0)
    execution_time_ms = fields.Float(
        dump_default=0.0,
        metadata={"description": "Database query execution time in milliseconds"},
    )
    error = fields.String(
        allow_none=True,
        metadata={"description": "Sanitized error message if failed"},
    )
    is_refusal = fields.Boolean(
        dump_default=False,
        metadata={"description": "True if user asked to modify data or violation occurred"},
    )


class SchemaTableColumnSchema(Schema):
    name = fields.String(required=True)
    type = fields.String(required=True)
    nullable = fields.Boolean(required=True)
    primary_key = fields.Boolean(required=True)
    foreign_key = fields.String(allow_none=True)


class SchemaTableSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(allow_none=True)
    columns = fields.List(fields.Nested(SchemaTableColumnSchema))


class SchemaResponseSchema(Schema):
    tables = fields.List(fields.Nested(SchemaTableSchema))
