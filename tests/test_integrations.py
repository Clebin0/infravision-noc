from app.integrations.netbox import NetBoxClient
from app.integrations.zabbix import ZabbixClient


def test_netbox_v2_token_uses_bearer_scheme():
    client = NetBoxClient("https://netbox.example", "nbt_key.secret")
    assert client._headers()["Authorization"] == "Bearer nbt_key.secret"


def test_netbox_legacy_token_uses_token_scheme():
    client = NetBoxClient("https://netbox.example", "legacy-token")
    assert client._headers()["Authorization"] == "Token legacy-token"


def test_netbox_device_normalization():
    device = NetBoxClient.normalize_device({
        "id": 42,
        "name": "edge-sw-01",
        "status": {"value": "active", "label": "Active"},
        "site": {"name": "Curitiba"},
        "primary_ip4": {"address": "192.0.2.10/24"},
        "rack": {"name": "R01"},
        "position": 12,
    })
    assert device["external_id"] == "42"
    assert device["name"] == "edge-sw-01"
    assert device["site"] == "Curitiba"
    assert device["primary_ip"] == "192.0.2.10/24"


def test_zabbix_endpoint_is_normalized():
    client = ZabbixClient("https://zabbix.example/zabbix", "token")
    assert client.endpoint == "https://zabbix.example/zabbix/api_jsonrpc.php"


def test_unconfigured_integrations_are_detected():
    assert NetBoxClient(None, None).configured is False
    assert ZabbixClient(None, None).configured is False
