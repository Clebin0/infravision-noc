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
