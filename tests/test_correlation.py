from app.services.correlation import correlate_inventory


def device(name="edge-sw-01", primary_ip="192.0.2.10/24"):
    return {
        "external_id": "42",
        "name": name,
        "primary_ip": primary_ip,
        "source": "netbox",
    }


def host(external_id, technical_name, ip, name=None):
    return {
        "external_id": external_id,
        "technical_name": technical_name,
        "name": name or technical_name,
        "status": "enabled",
        "interfaces": [{"ip": ip, "dns": "", "main": "1"}],
        "source": "zabbix",
    }


def test_correlates_by_exact_hostname_first():
    result = correlate_inventory([device()], [host("1001", "EDGE-SW-01", "198.51.100.5")])
    row = result["results"][0]
    assert row["monitoring_status"] == "matched"
    assert row["match_method"] == "hostname"
    assert row["zabbix_hosts"][0]["external_id"] == "1001"


def test_correlates_by_normalized_management_ip():
    result = correlate_inventory(
        [device(name="edge-switch", primary_ip="192.0.2.10/24")],
        [host("1001", "switch-01", "192.0.2.10")],
    )
    row = result["results"][0]
    assert row["monitoring_status"] == "matched"
    assert row["match_method"] == "management_ip"


def test_ambiguous_hostname_is_not_silently_merged():
    result = correlate_inventory(
        [device()],
        [host("1001", "edge-sw-01", "192.0.2.11"), host("1002", "edge-sw-01", "192.0.2.12")],
    )
    row = result["results"][0]
    assert row["monitoring_status"] == "ambiguous"
    assert len(row["zabbix_hosts"]) == 2
    assert result["matched_count"] == 0


def test_unmatched_devices_and_hosts_are_reported():
    result = correlate_inventory(
        [device(name="new-router", primary_ip="192.0.2.99")],
        [host("1001", "old-router", "198.51.100.3")],
    )
    assert result["results"][0]["monitoring_status"] == "unmonitored"
    assert len(result["unmatched_zabbix_hosts"]) == 1
    assert result["unmonitored_count"] == 1


def test_same_zabbix_host_is_not_assigned_to_two_netbox_devices():
    result = correlate_inventory(
        [
            device(name="edge-sw-01", primary_ip="192.0.2.10"),
            device(name="EDGE-SW-01", primary_ip="192.0.2.20"),
        ],
        [host("1001", "edge-sw-01", "192.0.2.10")],
    )
    assert [row["monitoring_status"] for row in result["results"]] == ["ambiguous", "ambiguous"]
    assert result["matched_count"] == 0
    assert result["ambiguous_zabbix_host_count"] == 1
    assert result["unmatched_zabbix_host_count"] == 0


def test_ambiguous_zabbix_hosts_are_not_reported_as_unmatched():
    result = correlate_inventory(
        [device()],
        [
            host("1001", "edge-sw-01", "192.0.2.11"),
            host("1002", "edge-sw-01", "192.0.2.12"),
            host("1003", "unrelated-host", "198.51.100.3"),
        ],
    )
    assert result["results"][0]["monitoring_status"] == "ambiguous"
    assert result["ambiguous_zabbix_host_count"] == 2
    assert result["unmatched_zabbix_host_count"] == 1
    assert [item["external_id"] for item in result["unmatched_zabbix_hosts"]] == ["1003"]


def test_hostname_matching_has_priority_over_a_conflicting_ip_match():
    result = correlate_inventory(
        [device(name="edge-sw-01", primary_ip="192.0.2.10")],
        [
            host("1001", "edge-sw-01", "198.51.100.10"),
            host("1002", "another-host", "192.0.2.10"),
        ],
    )
    row = result["results"][0]
    assert row["monitoring_status"] == "matched"
    assert row["match_method"] == "hostname"
    assert [item["external_id"] for item in row["zabbix_hosts"]] == ["1001"]
