import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROVISIONING = ROOT / "grafana" / "provisioning"


def load_yaml(relative_path: str):
    with (PROVISIONING / relative_path).open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_zabbix_datasource_uses_read_only_token_from_environment():
    config = load_yaml("datasources/zabbix.yaml")
    datasource = config["datasources"][0]

    assert datasource["name"] == "Zabbix"
    assert datasource["uid"] == "infravision-zabbix"
    assert datasource["type"] == "alexanderzobnin-zabbix-datasource"
    assert datasource["url"] == "${ZABBIX_GRAFANA_URL}"
    assert datasource["jsonData"]["authType"] == "token"
    assert datasource["secureJsonData"]["apiToken"] == "${ZABBIX_GRAFANA_TOKEN}"
    assert datasource["editable"] is False


def test_zabbix_app_is_enabled_by_provisioning():
    config = load_yaml("plugins/zabbix-app.yaml")
    app = config["apps"][0]

    assert app["type"] == "alexanderzobnin-zabbix-app"
    assert app["org_id"] == 1
    assert app["disabled"] is False


def test_dashboard_provider_points_to_mounted_dashboard_directory():
    config = load_yaml("dashboards/provider.yaml")
    provider = config["providers"][0]

    assert provider["folder"] == "InfraVision NOC"
    assert provider["type"] == "file"
    assert provider["options"]["path"] == "/var/lib/grafana/dashboards"


def test_noc_dashboard_has_dynamic_group_host_filters_and_expected_panels():
    dashboard_path = ROOT / "grafana" / "dashboards" / "infravision-noc.json"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))

    assert dashboard["uid"] == "infravision-noc"
    assert dashboard["title"] == "InfraVision NOC - Zabbix Monitoring"
    assert {item["name"] for item in dashboard["templating"]["list"]} == {"group", "host"}

    variables = {item["name"]: item["query"] for item in dashboard["templating"]["list"]}
    assert variables["group"]["queryType"] == "group"
    assert variables["host"]["queryType"] == "host"
    assert variables["host"]["group"] == "$group"

    panels = dashboard["panels"]
    assert len(panels) == 5
    query_types = {
        target["queryType"]
        for panel in panels
        for target in panel.get("targets", [])
    }
    assert "0" in query_types
    assert "5" in query_types


def test_all_dashboard_panels_use_the_provisioned_zabbix_uid():
    dashboard_path = ROOT / "grafana" / "dashboards" / "infravision-noc.json"
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))

    for panel in dashboard["panels"]:
        assert panel["datasource"]["uid"] == "infravision-zabbix"
        for target in panel.get("targets", []):
            assert target["datasource"]["uid"] == "infravision-zabbix"
