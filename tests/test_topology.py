from app.integrations.netbox import NetBoxClient


def endpoint(
    interface_id: int,
    interface_name: str,
    device_id: int,
    device_name: str,
    *,
    site: str = "Curitiba DC",
):
    return {
        "object_type": "dcim.interface",
        "object_id": interface_id,
        "object": {
            "id": interface_id,
            "name": interface_name,
            "label": "",
            "type": {"value": "1000base-t", "label": "1GBASE-T"},
            "enabled": True,
            "device": {
                "id": device_id,
                "name": device_name,
                "display": device_name,
                "device_type": {"model": "Switch", "display": "Network switch"},
                "role": {"name": "Network"},
                "site": {"name": site},
                "status": {"value": "active", "label": "Active"},
            },
        },
    }


def cable(cable_id: int, a, b, **extra):
    return {
        "id": cable_id,
        "label": f"CAT6-{cable_id:03}",
        "status": {"value": "connected", "label": "Connected"},
        "type": {"value": "cat6", "label": "Cat6"},
        "a_terminations": a,
        "b_terminations": b,
        **extra,
    }


def test_normalizes_direct_device_interface_connection():
    payload = NetBoxClient.normalize_topology([
        cable(
            17,
            [endpoint(101, "Gi1/0/1", 1, "core-sw-01")],
            [endpoint(202, "Gi1/0/24", 2, "dist-sw-01")],
            color="00aa88",
            length=3,
            length_unit={"value": "m", "label": "Meters"},
        )
    ])

    assert payload["device_count"] == 2
    assert payload["connection_count"] == 1
    assert payload["unsupported_cable_count"] == 0
    assert [node["name"] for node in payload["nodes"]] == ["core-sw-01", "dist-sw-01"]

    link = payload["links"][0]
    assert link["cable_id"] == "17"
    assert link["status"] == "Connected"
    assert link["type"] == "Cat6"
    assert link["length_unit"] == "Meters"
    assert link["a"]["interface_name"] == "Gi1/0/1"
    assert link["b"]["device_name"] == "dist-sw-01"


def test_ignores_non_interface_terminations_and_reports_unsupported_cables():
    payload = NetBoxClient.normalize_topology([
        cable(
            18,
            [endpoint(103, "Gi1/0/3", 1, "core-sw-01")],
            [{"object_type": "dcim.frontport", "object_id": 304, "object": {"name": "Front 1"}}],
        )
    ])

    assert payload["nodes"] == []
    assert payload["links"] == []
    assert payload["connection_count"] == 0
    assert payload["unsupported_cable_count"] == 1


def test_handles_breakout_cables_with_multiple_interface_terminations():
    payload = NetBoxClient.normalize_topology([
        cable(
            19,
            [
                endpoint(111, "Eth1/1/1", 1, "spine-01"),
                endpoint(112, "Eth1/1/2", 1, "spine-01"),
            ],
            [endpoint(221, "Eth1/49", 2, "leaf-01")],
        )
    ])

    assert payload["device_count"] == 2
    assert payload["connection_count"] == 2
    spine = next(node for node in payload["nodes"] if node["name"] == "spine-01")
    assert len(spine["interfaces"]) == 2
    assert {link["a"]["interface_name"] for link in payload["links"]} == {"Eth1/1/1", "Eth1/1/2"}


def test_deduplicates_shared_device_nodes_and_interface_records():
    payload = NetBoxClient.normalize_topology([
        cable(20, [endpoint(101, "Gi1/0/1", 1, "switch-01")], [endpoint(202, "Gi1/0/1", 2, "switch-02")]),
        cable(21, [endpoint(102, "Gi1/0/2", 1, "switch-01")], [endpoint(203, "Gi1/0/2", 3, "switch-03")]),
    ])

    assert payload["device_count"] == 3
    switch = next(node for node in payload["nodes"] if node["name"] == "switch-01")
    assert switch["interface_count"] == 2
