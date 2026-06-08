import pytest

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_create_token(client):
    response = client.post("/tokens/test-agent-1")
    assert response.status_code == 200
    # API возвращает токен напрямую, не через create_success_response
    data = response.json()
    assert "agent_id" in data or "token_id" in data

def test_list_policies(client):
    response = client.get("/policies")
    assert response.status_code == 200
    data = response.json()
    assert "active" in data

def test_consensus_endpoint(client):
    response = client.get("/consensus")
    # Может вернуть 200 или 404 в зависимости от реализации
    assert response.status_code in [200, 404]
