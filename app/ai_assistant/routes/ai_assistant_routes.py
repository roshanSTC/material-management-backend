"""API routes for AI Database Assistant."""

from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from app.ai_assistant.models.ai_assistant_models import (
    QueryRequestSchema,
    QueryResponseSchema,
    SchemaResponseSchema,
)
from app.ai_assistant.services.ai_service import AIService
from app.ai_assistant.services.schema_service import SchemaService

ai_assistant_bp = Blueprint(
    "ai_assistant",
    __name__,
    url_prefix="/api/v1/ai-assistant",
    description="Read-Only AI Database Assistant APIs",
)


@ai_assistant_bp.post("/query")
@ai_assistant_bp.doc(security=[{"BearerAuth": []}])
@ai_assistant_bp.arguments(QueryRequestSchema)
@ai_assistant_bp.response(200, QueryResponseSchema)
@jwt_required()
def query_database(data):
    """
    Query the database using natural language.

    The question is translated into a safe, read-only SQL query, validated,
    and executed against the database under strict read-only constraints.
    """
    user_id = get_jwt_identity()
    question = data.get("question", "").strip()
    history = data.get("history", [])

    result = AIService.process_query(
        question=question,
        user_id=str(user_id) if user_id else None,
        history=history,
    )
    return result


@ai_assistant_bp.get("/schema")
@ai_assistant_bp.doc(security=[{"BearerAuth": []}])
@ai_assistant_bp.response(200, SchemaResponseSchema)
@jwt_required()
def get_schema():
    """
    Get non-sensitive database schema metadata and table descriptions.
    """
    tables = SchemaService.get_tables_metadata()
    return {"tables": tables}


@ai_assistant_bp.get("/health")
def health_check():
    """Check AI assistant health and readiness."""
    return {
        "status": "healthy",
        "service": "ai-assistant",
        "read_only": True,
    }
