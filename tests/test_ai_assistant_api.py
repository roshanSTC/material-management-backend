"""API endpoint integration tests for /api/v1/ai-assistant."""

import pytest
from unittest.mock import patch
from flask_jwt_extended import create_access_token
from app import create_app
from app.config.settings import Config


class ApiTestConfig(Config):
    TESTING = True
    JWT_SECRET_KEY = "test-jwt-secret-key-12345"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def test_app():
    app = create_app(ApiTestConfig)
    return app


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def auth_header(test_app):
    with test_app.app_context():
        token = create_access_token(identity="test-user-1")
        return {"Authorization": f"Bearer {token}"}


class TestAIAssistantAPI:
    """Test suite verifying endpoint security and request processing."""

    def test_health_check_endpoint(self, client):
        res = client.get("/api/v1/ai-assistant/health")
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "healthy"
        assert data["read_only"] is True

    def test_query_requires_jwt_authentication(self, client):
        res = client.post(
            "/api/v1/ai-assistant/query",
            json={"question": "Show all customers"},
        )
        assert res.status_code == 401

    def test_schema_requires_jwt_authentication(self, client):
        res = client.get("/api/v1/ai-assistant/schema")
        assert res.status_code == 401

    @patch("app.ai_assistant.services.query_executor.QueryExecutor.execute")
    def test_authenticated_query_returns_structured_table(self, mock_exec, client, auth_header):
        mock_exec.return_value = (
            ["id", "name"],
            [{"id": 1, "name": "Stantech Corp"}],
            12.5,
        )

        res = client.post(
            "/api/v1/ai-assistant/query",
            json={"question": "Show top 10 customers"},
            headers=auth_header,
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["type"] == "table"
        assert len(data["rows"]) == 1
        assert data["columns"] == ["id", "name"]
        assert data["rows"][0]["name"] == "Stantech Corp"

    def test_authenticated_refusal_for_delete_request(self, client, auth_header):
        res = client.post(
            "/api/v1/ai-assistant/query",
            json={"question": "Delete all customers from database"},
            headers=auth_header,
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["is_refusal"] is True
        assert "cannot modify, delete, or update database records" in data["summary"]
        assert data["rows"] == []

    def test_authenticated_schema_retrieval(self, client, auth_header):
        res = client.get(
            "/api/v1/ai-assistant/schema",
            headers=auth_header,
        )
        assert res.status_code == 200
        data = res.get_json()
        assert "tables" in data
        assert isinstance(data["tables"], list)
