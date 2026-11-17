from collections import Counter
from ipaddress import ip_address, ip_interface
from typing import Any


def _normalized_name(value: Any) -> str:
    return str(value or "").strip().rstrip(".").casefold()


def _normalized_ip(value: Any) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return str(ip_interface(raw).ip if "/" in raw else ip_address(raw))
    except ValueError:
        return None


def _host_names(host: dict[str, Any]) -> set[str]:
    return {
        name
        for name in (
            _normalized_name(host.get("technical_name")),
            _normalized_name(host.get("name")),
        )
        if name
    }


def _host_ips(host: dict[str, Any]) -> set[str]:
    addresses: set[str] = set()
    for interface in host.get("interfaces") or []:
        address = _normalized_ip(interface.get("ip"))
        if address and address != "0.0.0.0":
            addresses.add(address)
    return addresses


def correlate_inventory(
    netbox_devices: list[dict[str, Any]],
    zabbix_hosts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Correlate NetBox devices to Zabbix hosts without guessing ambiguous matches.

    Matching priority:
    1. Exact, case-insensitive NetBox device name against Zabbix technical/display name.
    2. Exact normalized management IP against Zabbix interface IP values.

    Many-to-one and one-to-many matches are marked ambiguous. No ambiguous
    relationship is selected automatically.
    """
    indexed_hosts = [
        {
            "host": host,
            "names": _host_names(host),
            "ips": _host_ips(host),
            "id": str(host.get("external_id") or host.get("technical_name") or f"zabbix-index-{index}"),
        }
        for index, host in enumerate(zabbix_hosts)
    ]

    candidate_rows: list[dict[str, Any]] = []
    for device in netbox_devices:
        device_name = _normalized_name(device.get("name"))
        candidates = [
            entry for entry in indexed_hosts
            if device_name and device_name in entry["names"]
        ]
        match_method: str | None = "hostname" if candidates else None

        if not candidates:
            device_ip = _normalized_ip(device.get("primary_ip"))
            candidates = [
                entry for entry in indexed_hosts
                if device_ip and device_ip in entry["ips"]
            ]
            if candidates:
                match_method = "management_ip"

        unique = {entry["id"]: entry for entry in candidates}
        candidate_rows.append({
            "device": device,
            "candidates": list(unique.values()),
            "match_method": match_method if unique else None,
        })

    # Detect a Zabbix host that could be assigned to more than one NetBox asset.
    candidate_usage = Counter(
        candidate["id"]
        for row in candidate_rows
        for candidate in row["candidates"]
    )

    rows: list[dict[str, Any]] = []
    matched_ids: set[str] = set()
    ambiguous_ids: set[str] = set()
    matched_count = 0
    ambiguous_count = 0

    for row in candidate_rows:
        candidates = row["candidates"]
        ambiguity_reason: str | None = None

        if not candidates:
            match_status = "unmonitored"
        elif len(candidates) > 1:
            match_status = "ambiguous"
            ambiguity_reason = "multiple_zabbix_hosts"
        elif candidate_usage[candidates[0]["id"]] > 1:
            match_status = "ambiguous"
            ambiguity_reason = "multiple_netbox_devices"
        else:
            match_status = "matched"
            matched_count += 1
            matched_ids.add(candidates[0]["id"])

        if match_status == "ambiguous":
            ambiguous_count += 1
            ambiguous_ids.update(candidate["id"] for candidate in candidates)

        rows.append({
            **row["device"],
            "monitoring_status": match_status,
            "match_method": row["match_method"],
            "ambiguity_reason": ambiguity_reason,
            "zabbix_hosts": [
                {
                    "external_id": entry["host"].get("external_id"),
                    "technical_name": entry["host"].get("technical_name"),
                    "name": entry["host"].get("name"),
                    "status": entry["host"].get("status"),
                }
                for entry in candidates
            ],
        })

    unmatched_hosts = [
        host for entry in indexed_hosts
        if entry["id"] not in matched_ids and entry["id"] not in ambiguous_ids
        for host in [entry["host"]]
    ]
    ambiguous_hosts = [
        entry["host"] for entry in indexed_hosts if entry["id"] in ambiguous_ids
    ]

    return {
        "results": rows,
        "netbox_count": len(netbox_devices),
        "zabbix_host_count": len(zabbix_hosts),
        "matched_count": matched_count,
        "ambiguous_count": ambiguous_count,
        "unmonitored_count": len(netbox_devices) - matched_count - ambiguous_count,
        "unmatched_zabbix_host_count": len(unmatched_hosts),
        "ambiguous_zabbix_host_count": len(ambiguous_hosts),
        "unmatched_zabbix_hosts": unmatched_hosts,
        "ambiguous_zabbix_hosts": ambiguous_hosts,
    }
