import asyncio

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.integrations.netbox import NetBoxClient
from app.integrations.zabbix import ZabbixClient
from app.services.correlation import correlate_inventory
from app.settings import settings

router = APIRouter(prefix="/api", tags=["integrations"])

netbox = NetBoxClient(settings.netbox_url, settings.netbox_token)
zabbix = ZabbixClient(settings.zabbix_url, settings.zabbix_token)


@router.get("/integrations/status")
async def integration_status():
    netbox_status, zabbix_status = await asyncio.gather(
        netbox.health(),
        zabbix.health(),
    )
    return {
        "netbox": netbox_status,
        "zabbix": zabbix_status,
        "demo_mode": not (netbox.configured and zabbix.configured),
    }


@router.get("/inventory/devices")
async def inventory_devices(limit: int = Query(default=100, ge=1, le=500)):
    if not netbox.configured:
        return {"source": "demo", "demo": True, "count": 0, "results": []}
    try:
        result = await netbox.get_devices(limit=limit)
        return {"source": "netbox", "demo": False, **result}
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NetBox API request failed") from None


@router.get("/inventory/racks")
async def inventory_racks(limit: int = Query(default=200, ge=1, le=500)):
    if not netbox.configured:
        return {"source": "demo", "demo": True, "count": 0, "has_more": False, "results": []}
    try:
        result = await netbox.get_racks(limit=limit)
        return {"source": "netbox", "demo": False, **result}
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NetBox rack query failed") from None


@router.get("/inventory/racks/{rack_id}/devices")
async def rack_devices(rack_id: int, limit: int = Query(default=200, ge=1, le=500)):
    if not netbox.configured:
        return {"source": "demo", "demo": True, "count": 0, "has_more": False, "results": []}
    try:
        result = await netbox.get_rack_devices(rack_id=rack_id, limit=limit)
        return {"source": "netbox", "demo": False, **result}
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NetBox rack device query failed") from None


@router.get("/topology/connections")
async def topology_connections(limit: int = Query(default=500, ge=1, le=500)):
    if not netbox.configured:
        return {
            "source": "demo",
            "demo": True,
            "message": "Configure NetBox to load live cable and interface connections.",
            "nodes": [],
            "links": [],
            "connection_count": 0,
            "device_count": 0,
            "unsupported_cable_count": 0,
            "cable_count": 0,
            "returned_cable_count": 0,
            "has_more": False,
        }
    try:
        result = await netbox.get_topology(limit=limit)
        return {"source": "netbox", "demo": False, **result}
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NetBox topology query failed") from None


@router.get("/topology/monitoring")
async def topology_monitoring(limit: int = Query(default=500, ge=1, le=500)):
    if not netbox.configured:
        return {
            "source": "demo",
            "demo": True,
            "monitoring_source": "not_configured",
            "monitoring_message": "Configure NetBox to load physical connections.",
            "nodes": [],
            "links": [],
            "connection_count": 0,
            "device_count": 0,
            "unsupported_cable_count": 0,
            "cable_count": 0,
            "returned_cable_count": 0,
            "has_more": False,
            "matched_count": 0,
            "ambiguous_count": 0,
            "unmonitored_count": 0,
            "active_trigger_count": 0,
        }

    try:
        topology = await netbox.get_topology(limit=limit)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NetBox topology query failed") from None

    if not zabbix.configured:
        for node in topology["nodes"]:
            node.update({
                "monitoring_status": "not_configured",
                "monitoring_availability": "not_configured",
                "zabbix_host": None,
                "zabbix_candidates": [],
                "active_trigger_count": 0,
                "critical_trigger_count": 0,
                "warning_trigger_count": 0,
            })
        return {
            "source": "netbox",
            "demo": False,
            "monitoring_source": "not_configured",
            "monitoring_message": "NetBox topology is live. Configure Zabbix to overlay host availability and active problems.",
            **topology,
            "matched_count": 0,
            "ambiguous_count": 0,
            "unmonitored_count": len(topology["nodes"]),
            "active_trigger_count": 0,
        }

    try:
        hosts, triggers = await asyncio.gather(
            zabbix.get_hosts(),
            zabbix.get_active_triggers(),
        )
    except (httpx.HTTPError, RuntimeError, ValueError):
        for node in topology["nodes"]:
            node.update({
                "monitoring_status": "unavailable",
                "monitoring_availability": "unknown",
                "zabbix_host": None,
                "zabbix_candidates": [],
                "active_trigger_count": 0,
                "critical_trigger_count": 0,
                "warning_trigger_count": 0,
            })
        return {
            "source": "netbox",
            "demo": False,
            "monitoring_source": "unavailable",
            "monitoring_message": "NetBox topology is live, but the Zabbix API could not be queried.",
            **topology,
            "matched_count": 0,
            "ambiguous_count": 0,
            "unmonitored_count": len(topology["nodes"]),
            "active_trigger_count": 0,
        }

    correlation = correlate_inventory(topology["nodes"], hosts)
    hosts_by_id = {str(host.get("external_id")): host for host in hosts}
    trigger_counts: dict[str, dict[str, int]] = {}
    for trigger in triggers:
        try:
            priority = int(trigger.get("priority") or 0)
        except (TypeError, ValueError):
            priority = 0
        for host in trigger.get("hosts") or []:
            host_id = str(host.get("hostid") or "")
            if not host_id:
                continue
            counts = trigger_counts.setdefault(host_id, {"active": 0, "critical": 0, "warning": 0})
            counts["active"] += 1
            if priority >= 4:
                counts["critical"] += 1
            elif priority in (2, 3):
                counts["warning"] += 1

    enriched_nodes = []
    for node in correlation["results"]:
        candidates = node.get("zabbix_hosts") or []
        match = hosts_by_id.get(str(candidates[0].get("external_id"))) if len(candidates) == 1 else None
        host_id = str(match.get("external_id")) if match else ""
        counts = trigger_counts.get(host_id, {"active": 0, "critical": 0, "warning": 0})
        if node.get("monitoring_status") == "matched" and match:
            monitoring_status = "matched"
            availability = match.get("availability") or "unknown"
        elif node.get("monitoring_status") == "ambiguous":
            monitoring_status = "ambiguous"
            availability = "unknown"
        else:
            monitoring_status = "unmonitored"
            availability = "unknown"

        enriched_nodes.append({
            **node,
            "monitoring_status": monitoring_status,
            "monitoring_availability": availability,
            "zabbix_host": ({
                "external_id": match.get("external_id"),
                "technical_name": match.get("technical_name"),
                "name": match.get("name"),
                "status": match.get("status"),
                "availability": match.get("availability"),
            } if match else None),
            "zabbix_candidates": candidates if monitoring_status == "ambiguous" else [],
            "active_trigger_count": counts["active"] if match else 0,
            "critical_trigger_count": counts["critical"] if match else 0,
            "warning_trigger_count": counts["warning"] if match else 0,
        })

    return {
        "source": "netbox+zabbix",
        "demo": False,
        "monitoring_source": "zabbix",
        "monitoring_message": "Physical links from NetBox; host availability and active problems from Zabbix.",
        **{key: value for key, value in topology.items() if key != "nodes"},
        "nodes": enriched_nodes,
        "matched_count": correlation["matched_count"],
        "ambiguous_count": correlation["ambiguous_count"],
        "unmonitored_count": correlation["unmonitored_count"],
        "active_trigger_count": len(triggers),
    }


@router.get("/monitoring/hosts")
async def monitoring_hosts():
    if not zabbix.configured:
        return {"source": "demo", "demo": True, "count": 0, "results": []}
    try:
        results = await zabbix.get_hosts()
        return {"source": "zabbix", "demo": False, "count": len(results), "results": results}
    except (httpx.HTTPError, RuntimeError):
        raise HTTPException(status_code=502, detail="Zabbix API request failed") from None


@router.get("/monitoring/triggers")
async def monitoring_triggers():
    if not zabbix.configured:
        return {"source": "demo", "demo": True, "count": 0, "results": []}
    try:
        results = await zabbix.get_active_triggers()
        return {"source": "zabbix", "demo": False, "count": len(results), "results": results}
    except (httpx.HTTPError, RuntimeError):
        raise HTTPException(status_code=502, detail="Zabbix trigger query failed") from None


@router.get("/monitoring/hosts/{host_id}/metrics")
async def monitoring_host_metrics(
    host_id: str,
    limit: int = Query(default=200, ge=1, le=500),
):
    if not zabbix.configured:
        return {
            "source": "demo",
            "demo": True,
            "host_id": host_id,
            "count": 0,
            "metrics": [],
            "summary": {
                "cpu": [],
                "memory": [],
                "disk": [],
                "network_in": [],
                "network_out": [],
            },
        }
    try:
        result = await zabbix.get_latest_metrics(host_id=host_id, limit=limit)
        return {"demo": False, **result}
    except (httpx.HTTPError, RuntimeError, ValueError):
        raise HTTPException(status_code=502, detail="Zabbix host metrics query failed") from None


@router.get("/correlation/inventory")
@router.get("/correlation/devices", include_in_schema=False)
async def correlated_inventory(limit: int = Query(default=200, ge=1, le=500)):
    if not netbox.configured or not zabbix.configured:
        return {
            "source": "demo",
            "demo": True,
            "message": "Configure both NetBox and Zabbix to enable live inventory correlation.",
            "results": [],
            "netbox_count": 0,
            "zabbix_host_count": 0,
            "matched_count": 0,
            "ambiguous_count": 0,
            "unmonitored_count": 0,
            "unmatched_zabbix_hosts": [],
        }
    try:
        inventory, hosts = await asyncio.gather(
            netbox.get_devices(limit=limit),
            zabbix.get_hosts(),
        )
    except (httpx.HTTPError, RuntimeError):
        raise HTTPException(status_code=502, detail="Unable to retrieve inventory correlation data") from None

    return {
        "source": "netbox+zabbix",
        "demo": False,
        **correlate_inventory(inventory["results"], hosts),
    }
