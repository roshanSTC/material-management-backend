"""Unit tests for AI Assistant Service and Prompt Service."""

import pytest
from unittest.mock import patch, MagicMock
from app.ai_assistant.services.ai_service import AIService
from app.ai_assistant.services.prompt_service import PromptService, SAFE_REFUSAL_TEXT
from app.ai_assistant.services.schema_service import SchemaService
from app.ai_assistant.services.sql_generator import SQLGenerator


class TestPromptAndSchemaService:
    """Tests for prompt engineering and schema privacy guarantees."""

    def test_preflight_refusal_patterns(self):
        refusal = PromptService.check_preflight_refusal("Delete all customers from database")
        assert refusal == SAFE_REFUSAL_TEXT

        refusal = PromptService.check_preflight_refusal("Drop table projects")
        assert refusal == SAFE_REFUSAL_TEXT

        refusal = PromptService.check_preflight_refusal("Update customer 1 email to test@hack.com")
        assert refusal == SAFE_REFUSAL_TEXT

        refusal = PromptService.check_preflight_refusal("Truncate suppliers table")
        assert refusal == SAFE_REFUSAL_TEXT

    def test_valid_question_passes_preflight(self):
        assert PromptService.check_preflight_refusal("Show top 10 customers by order value") is None
        assert PromptService.check_preflight_refusal("How many active projects do we have?") is None
        assert PromptService.check_preflight_refusal("What is the total revenue for this month?") is None

    def test_schema_never_includes_sensitive_passwords(self):
        metadata = SchemaService.get_tables_metadata()
        for table in metadata:
            column_names = [col["name"].lower() for col in table["columns"]]
            assert "password" not in column_names
            assert "password_hash" not in column_names
            assert "jwt_secret" not in column_names
            assert "api_key" not in column_names

    def test_prompt_schema_context_contains_expected_tables(self):
        context = SchemaService.get_prompt_schema_context()
        assert "Table: customers" in context
        assert "Database Schema (PostgreSQL):" in context


class TestAIServiceFlow:
    """Tests for end-to-end AIService execution logic."""

    def test_modification_question_returns_safe_refusal(self):
        result = AIService.process_query(
            question="Drop table customers",
            user_id="user-123",
        )
        assert result["success"] is True
        assert result["is_refusal"] is True
        assert result["summary"] == SAFE_REFUSAL_TEXT
        assert result["sql"] is None
        assert result["rows"] == []

    @patch("app.ai_assistant.services.query_executor.QueryExecutor.execute")
    def test_valid_query_executes_safely(self, mock_execute):
        mock_execute.return_value = (
            ["id", "name", "city"],
            [
                {"id": 1, "name": "Acme Corp", "city": "Mumbai"},
                {"id": 2, "name": "Global Tech", "city": "Delhi"},
            ],
            14.2,
        )

        result = AIService.process_query(
            question="Show all customers in Mumbai",
            user_id="user-123",
        )
        assert result["success"] is True
        assert result["is_refusal"] is False
        assert result["total_rows"] == 2
        assert len(result["rows"]) == 2
        assert result["columns"] == ["id", "name", "city"]
        assert "SELECT" in result["sql"].upper()

    @patch("app.ai_assistant.services.sql_generator.SQLGenerator.generate_sql")
    def test_malicious_sql_from_llm_is_caught_and_rejected(self, mock_gen):
        # Even if LLM hallucinations produce a DELETE statement
        mock_gen.return_value = (
            "DELETE FROM customers WHERE id = 10",
            "Deleting the customer",
            None,
        )

        result = AIService.process_query(
            question="Remove customer 10",
            user_id="user-123",
        )
        assert result["success"] is False
        assert result["is_refusal"] is True
        assert "Database modifications are not allowed" in result["error"]
        assert result["rows"] == []
