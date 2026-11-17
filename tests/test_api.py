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


def test_topology_endpoint_returns_empty_demo_graph_when_netbox_is_unconfigured():
    response = client.get("/api/topology/connections")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "demo"
    assert payload["demo"] is True
    assert payload["nodes"] == []
    assert payload["links"] == []
    assert payload["connection_count"] == 0
    assert payload["unsupported_cable_count"] == 0


def test_topology_monitoring_keeps_live_netbox_data_when_zabbix_is_not_configured(monkeypatch):
    from app.api import routes

    class FakeNetBox:
        configured = True

        async def get_topology(self, limit=500):
            return {
                "nodes": [{
                    "id": "1", "name": "core-sw-01", "primary_ip": "192.0.2.10/24",
                    "interfaces": [], "interface_count": 0, "site": "Curitiba",
                }],
                "links": [], "connection_count": 0, "device_count": 1,
                "unsupported_cable_count": 0, "cable_count": 0,
                "returned_cable_count": 0, "has_more": False,
            }

    class FakeZabbix:
        configured = False

    monkeypatch.setattr(routes, "netbox", FakeNetBox())
    monkeypatch.setattr(routes, "zabbix", FakeZabbix())

    response = client.get("/api/topology/monitoring")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "netbox"
    assert payload["demo"] is False
    assert payload["monitoring_source"] == "not_configured"
    assert payload["nodes"][0]["monitoring_status"] == "not_configured"


def test_topology_monitoring_enriches_nodes_with_zabbix_availability_and_triggers(monkeypatch):
    from app.api import routes

    class FakeNetBox:
        configured = True

        async def get_topology(self, limit=500):
            return {
                "nodes": [{
                    "id": "1", "name": "core-sw-01", "primary_ip": "192.0.2.10/24",
                    "interfaces": [], "interface_count": 0, "site": "Curitiba",
                }],
                "links": [], "connection_count": 0, "device_count": 1,
                "unsupported_cable_count": 0, "cable_count": 0,
                "returned_cable_count": 0, "has_more": False,
            }

    class FakeZabbix:
        configured = True

        async def get_hosts(self):
            return [{
                "external_id": "1001", "technical_name": "CORE-SW-01",
                "name": "Core switch 01", "status": "enabled",
                "availability": "available",
                "interfaces": [{"ip": "192.0.2.10", "available": "1", "availability": "available"}],
            }]

        async def get_active_triggers(self):
            return [
                {
                    "external_id": "9001", "title": "High CPU",
                    "priority": "4", "hosts": [{"hostid": "1001", "host": "CORE-SW-01"}],
                },
                {
                    "external_id": "9002", "title": "Packet errors",
                    "priority": "3", "hosts": [{"hostid": "1001", "host": "CORE-SW-01"}],
                },
            ]

    monkeypatch.setattr(routes, "netbox", FakeNetBox())
    monkeypatch.setattr(routes, "zabbix", FakeZabbix())

    response = client.get("/api/topology/monitoring")
    assert response.status_code == 200
    payload = response.json()
    node = payload["nodes"][0]
    assert payload["source"] == "netbox+zabbix"
    assert payload["monitoring_source"] == "zabbix"
    assert payload["matched_count"] == 1
    assert node["monitoring_status"] == "matched"
    assert node["monitoring_availability"] == "available"
    assert node["active_trigger_count"] == 2
    assert node["critical_trigger_count"] == 1
    assert node["warning_trigger_count"] == 1
    assert payload["active_trigger_count"] == 2


def test_host_metrics_endpoint_returns_empty_demo_result_when_zabbix_is_unconfigured():
    response = client.get("/api/monitoring/hosts/1001/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is True
    assert payload["host_id"] == "1001"
    assert payload["count"] == 0
    assert payload["metrics"] == []
    assert payload["summary"]["cpu"] == []


def test_topology_monitoring_preserves_live_netbox_graph_when_zabbix_is_unreachable(monkeypatch):
    from app.api import routes

    class FakeNetBox:
        configured = True

        async def get_topology(self, limit=500):
            return {
                "nodes": [{
                    "id": "1", "name": "core-sw-01", "primary_ip": "192.0.2.10/24",
                    "interfaces": [], "interface_count": 0, "site": "Curitiba",
                }],
                "links": [], "connection_count": 0, "device_count": 1,
                "unsupported_cable_count": 0, "cable_count": 0,
                "returned_cable_count": 0, "has_more": False,
            }

    class FakeZabbix:
        configured = True

        async def get_hosts(self):
            raise RuntimeError("Zabbix token rejected")

        async def get_active_triggers(self):
            raise RuntimeError("Zabbix token rejected")

    monkeypatch.setattr(routes, "netbox", FakeNetBox())
    monkeypatch.setattr(routes, "zabbix", FakeZabbix())

    response = client.get("/api/topology/monitoring")
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "netbox"
    assert payload["demo"] is False
    assert payload["monitoring_source"] == "unavailable"
    assert payload["nodes"][0]["monitoring_status"] == "unavailable"
    assert payload["device_count"] == 1


def test_topology_monitoring_does_not_assign_ambiguous_zabbix_hosts(monkeypatch):
    from app.api import routes

    class FakeNetBox:
        configured = True

        async def get_topology(self, limit=500):
            return {
                "nodes": [{
                    "id": "1", "name": "core-sw-01", "primary_ip": "192.0.2.10/24",
                    "interfaces": [], "interface_count": 0, "site": "Curitiba",
                }],
                "links": [], "connection_count": 0, "device_count": 1,
                "unsupported_cable_count": 0, "cable_count": 0,
                "returned_cable_count": 0, "has_more": False,
            }

    class FakeZabbix:
        configured = True

        async def get_hosts(self):
            return [
                {"external_id": "1001", "technical_name": "core-sw-01", "name": "Core 01", "status": "enabled", "availability": "available", "interfaces": []},
                {"external_id": "1002", "technical_name": "CORE-SW-01", "name": "Core 01 duplicate", "status": "enabled", "availability": "unavailable", "interfaces": []},
            ]

        async def get_active_triggers(self):
            return []

    monkeypatch.setattr(routes, "netbox", FakeNetBox())
    monkeypatch.setattr(routes, "zabbix", FakeZabbix())

    response = client.get("/api/topology/monitoring")
    assert response.status_code == 200
    node = response.json()["nodes"][0]
    assert node["monitoring_status"] == "ambiguous"
    assert node["monitoring_availability"] == "unknown"
    assert node["zabbix_host"] is None
    assert len(node["zabbix_candidates"]) == 2


def test_host_metrics_endpoint_returns_latest_zabbix_items_for_a_configured_host(monkeypatch):
    from app.api import routes

    class FakeZabbix:
        configured = True

        async def get_latest_metrics(self, host_id, limit=200):
            return {
                "host_id": str(host_id),
                "count": 1,
                "metrics": [{
                    "item_id": "501",
                    "name": "CPU utilization",
                    "key": "system.cpu.util",
                    "category": "cpu",
                    "value": "21.5",
                    "numeric_value": 21.5,
                    "units": "%",
                    "last_clock": 1730000000,
                    "value_type": "0",
                    "source": "zabbix",
                }],
                "summary": {"cpu": [{"item_id": "501", "value": "21.5", "units": "%"}], "memory": [], "disk": [], "network_in": [], "network_out": []},
                "source": "zabbix",
            }

    monkeypatch.setattr(routes, "zabbix", FakeZabbix())
    response = client.get("/api/monitoring/hosts/1001/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["demo"] is False
    assert payload["host_id"] == "1001"
    assert payload["count"] == 1
    assert payload["metrics"][0]["category"] == "cpu"
    assert payload["metrics"][0]["numeric_value"] == 21.5


def test_host_metrics_endpoint_reports_upstream_failure_without_fake_values(monkeypatch):
    from app.api import routes

    class FakeZabbix:
        configured = True

        async def get_latest_metrics(self, host_id, limit=200):
            raise RuntimeError("Zabbix API unavailable")

    monkeypatch.setattr(routes, "zabbix", FakeZabbix())
    response = client.get("/api/monitoring/hosts/1001/metrics")
    assert response.status_code == 502
    assert response.json()["detail"] == "Zabbix host metrics query failed"
