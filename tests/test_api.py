from fastapi.testclient import TestClient

from app.main import app

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


def test_integration_status_reports_unconfigured_providers():
    response = client.get("/api/integrations/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["netbox"]["configured"] is False
    assert payload["zabbix"]["configured"] is False
    assert payload["demo_mode"] is True


def test_inventory_endpoint_does_not_fabricate_live_devices():
    response = client.get("/api/inventory/devices")
    assert response.status_code == 200
    assert response.json() == {
        "source": "demo",
        "demo": True,
        "count": 0,
        "results": [],
    }


def test_monitoring_endpoint_returns_empty_demo_hosts_when_unconfigured():
    response = client.get("/api/monitoring/hosts")
    assert response.status_code == 200
    assert response.json()["demo"] is True
    assert response.json()["results"] == []


def test_correlation_requires_both_providers_and_does_not_fake_live_matches():
    response = client.get("/api/correlation/devices")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is True
    assert payload["source"] == "demo"
    assert payload["results"] == []
    assert payload["matched_count"] == 0


def test_rack_inventory_endpoint_returns_empty_demo_result_when_unconfigured():
    response = client.get("/api/inventory/racks")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is True
    assert payload["results"] == []


def test_rack_devices_endpoint_returns_empty_demo_result_when_unconfigured():
    response = client.get("/api/inventory/racks/7/devices")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is True
    assert payload["results"] == []
