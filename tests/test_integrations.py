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


def test_zabbix_host_normalization_exposes_interface_availability():
    host = ZabbixClient.normalize_host({
        "hostid": "10084",
        "host": "core-sw-01",
        "name": "Core switch 01",
        "status": "0",
        "interfaces": [
            {"interfaceid": "201", "ip": "192.0.2.10", "main": "1", "available": "1"},
            {"interfaceid": "202", "ip": "192.0.2.11", "main": "0", "available": "2"},
        ],
    })
    assert host["availability"] == "partially_available"
    assert host["interfaces"][0]["availability"] == "available"
    assert host["interfaces"][1]["availability"] == "unavailable"


def test_zabbix_disabled_host_is_not_reported_as_available():
    host = ZabbixClient.normalize_host({
        "hostid": "10085",
        "host": "retired-host",
        "name": "Retired host",
        "status": "1",
        "interfaces": [{"interfaceid": "301", "ip": "192.0.2.20", "main": "1", "available": "1"}],
    })
    assert host["status"] == "disabled"
    assert host["availability"] == "disabled"


def test_zabbix_metric_normalization_classifies_cpu_memory_disk_and_network():
    fixtures = [
        {"itemid": "1", "name": "CPU utilization", "key_": "system.cpu.util", "lastvalue": "12.5", "lastclock": "1730000000", "units": "%"},
        {"itemid": "2", "name": "Memory utilization", "key_": "vm.memory.util", "lastvalue": "68", "units": "%"},
        {"itemid": "3", "name": "Root filesystem usage", "key_": "vfs.fs.size[/,pused]", "lastvalue": "81.2", "units": "%"},
        {"itemid": "4", "name": "Interface eth0: Bits received", "key_": "net.if.in[eth0]", "lastvalue": "1200", "units": "bps"},
        {"itemid": "5", "name": "Interface eth0: Bits sent", "key_": "net.if.out[eth0]", "lastvalue": "800", "units": "bps"},
    ]

    metrics = [ZabbixClient.normalize_item(item) for item in fixtures]
    assert [item["category"] for item in metrics] == [
        "cpu", "memory", "disk", "network_in", "network_out"
    ]
    assert metrics[0]["numeric_value"] == 12.5
    assert metrics[0]["last_clock"] == 1730000000
    assert metrics[0]["units"] == "%"
