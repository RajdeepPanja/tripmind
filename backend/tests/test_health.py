"""
Smoke test for Phase 1: confirms the app boots and the health route responds.
"""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "serpapi_key_configured" in body
    assert "groq_key_configured" in body