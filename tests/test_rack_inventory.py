from app.integrations.netbox import NetBoxClient


def test_netbox_rack_normalization():
    rack = NetBoxClient.normalize_rack({
        "id": 7,
        "name": "RACK-A01",
        "site": {"name": "Curitiba DC"},
        "tenant": {"name": "Example tenant"},
        "group": {"name": "Row A"},
        "status": {"value": "active", "label": "Active"},
        "u_height": 42,
        "width": 19,
        "facility": "DC-01",
    })
    assert rack["external_id"] == "7"
    assert rack["name"] == "RACK-A01"
    assert rack["site"] == "Curitiba DC"
    assert rack["u_height"] == 42
    assert rack["source"] == "netbox"


def test_netbox_device_normalization_exposes_rack_identifier():
    device = NetBoxClient.normalize_device({
        "id": 17,
        "name": "srv-01",
        "rack": {"id": 7, "name": "RACK-A01"},
        "position": 12,
        "face": "front",
    })
    assert device["rack_id"] == 7
    assert device["rack"] == "RACK-A01"
