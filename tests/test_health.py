"""Tests for GET /health endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Use context manager so lifespan runs and the model is loaded."""
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_field(self, client):
        data = client.get("/health").json()
        assert "status" in data
        assert data["status"] in ("healthy", "unhealthy")

    def test_health_reports_model_loaded(self, client):
        data = client.get("/health").json()
        assert "model_loaded" in data
        assert isinstance(data["model_loaded"], bool)
