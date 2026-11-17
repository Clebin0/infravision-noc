from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_overview_is_marked_as_demo_data():
    response = client.get("/api/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is True
    assert payload["kpis"]["devices_total"] >= payload["kpis"]["devices_online"]
    assert len(payload["devices"]) > 0
