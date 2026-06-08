
import pytest

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_create_token(client):
    response = client.post("/tokens/test-agent-1")
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is False
