import asyncio
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from app.integrations.netbox import NetBoxClient
from app.integrations.zabbix import ZabbixClient
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
async def inventory_devices(limit: int = 100):
    if not netbox.configured:
        return {"source": "demo", "demo": True, "count": 0, "results": []}
    try:
        result = await netbox.get_devices(limit=limit)
        return {"source": "netbox", "demo": False, **result}
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="NetBox API request failed") from None


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
        raise HTTPException(status_code=502, detail="Zabbix API request failed") from None
