from typing import Any

import httpx


class ZabbixClient:
    """Read-only Zabbix JSON-RPC client using an API token via Bearer auth."""

    def __init__(self, base_url: str | None, token: str | None, timeout: float = 10.0):
        base = (base_url or "").rstrip("/")
        self.endpoint = base if base.endswith("/api_jsonrpc.php") else f"{base}/api_jsonrpc.php" if base else ""
        self.token = token or ""
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json-rpc",
        }

    async def _call(self, method: str, params: dict[str, Any]) -> Any:
        if not self.configured:
            raise RuntimeError("Zabbix URL or API token not configured")

        request = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.endpoint, headers=self._headers(), json=request)
            response.raise_for_status()
            payload = response.json()

        if payload.get("error"):
            message = payload["error"].get("message", "Zabbix API request failed")
            data = payload["error"].get("data", "")
            raise RuntimeError(f"{message}: {data}".strip(": "))
        return payload.get("result")

    async def health(self) -> dict[str, Any]:
        if not self.configured:
            return {"configured": False, "reachable": False, "message": "URL or token not configured"}
        try:
            version = await self._call("apiinfo.version", {})
            return {"configured": True, "reachable": True, "message": "Zabbix API reachable", "version": version}
        except (httpx.HTTPError, RuntimeError, ValueError):
            return {"configured": True, "reachable": False, "message": "Zabbix API unavailable or authentication failed"}

    @staticmethod
    def normalize_host(host: dict[str, Any]) -> dict[str, Any]:
        availability_labels = {
            "0": "unknown",
            "1": "available",
            "2": "unavailable",
        }
        interfaces = []
        for interface in host.get("interfaces", []) or []:
            raw_available = interface.get("available")
            interfaces.append({
                "interface_id": interface.get("interfaceid"),
                "ip": interface.get("ip"),
                "dns": interface.get("dns"),
                "main": interface.get("main"),
                "type": interface.get("type"),
                "port": interface.get("port"),
                "available": raw_available,
                "availability": availability_labels.get(str(raw_available), "unknown"),
                "error": interface.get("error") or "",
            })

        monitored_interfaces = [item for item in interfaces if item["availability"] != "unknown"]
        has_available = any(item["availability"] == "available" for item in monitored_interfaces)
        has_unavailable = any(item["availability"] == "unavailable" for item in monitored_interfaces)

        if str(host.get("status", "0")) != "0":
            availability = "disabled"
        elif has_available and has_unavailable:
            availability = "partially_available"
        elif has_available:
            availability = "available"
        elif has_unavailable:
            availability = "unavailable"
        else:
            availability = "unknown"

        return {
            "external_id": str(host.get("hostid") or ""),
            "technical_name": host.get("host"),
            "name": host.get("name"),
            "status": "enabled" if str(host.get("status", "0")) == "0" else "disabled",
            "availability": availability,
            "interfaces": interfaces,
            "source": "zabbix",
        }

    async def get_hosts(self) -> list[dict[str, Any]]:
        result = await self._call(
            "host.get",
            {
                "output": ["hostid", "host", "name", "status"],
                "selectInterfaces": ["interfaceid", "ip", "dns", "main", "type", "port", "available", "error"],
                "sortfield": "host",
            },
        )
        return [self.normalize_host(host) for host in result or []]

    async def get_active_triggers(self) -> list[dict[str, Any]]:
        result = await self._call(
            "trigger.get",
            {
                "output": ["triggerid", "description", "priority", "lastchange", "value"],
                "filter": {"value": 1},
                "selectHosts": ["hostid", "host", "name"],
                "sortfield": "priority",
                "sortorder": "DESC",
            },
        )
        return [
            {
                "external_id": str(trigger.get("triggerid") or ""),
                "title": trigger.get("description"),
                "priority": trigger.get("priority"),
                "last_change": trigger.get("lastchange"),
                "hosts": trigger.get("hosts", []),
                "source": "zabbix",
            }
            for trigger in result or []
        ]


    @staticmethod
    def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
        name = str(item.get("name") or "Unnamed item")
        key = str(item.get("key_") or "")
        normalized = f"{name} {key}".casefold()

        if "system.cpu.util" in key.casefold() or "cpu utilization" in normalized or "cpu usage" in normalized:
            category = "cpu"
        elif "vm.memory.util" in key.casefold() or "memory utilization" in normalized or "memory usage" in normalized:
            category = "memory"
        elif "vfs.fs.size" in key.casefold() and ("pused" in key.casefold() or "utilization" in normalized):
            category = "disk"
        elif "net.if.in" in key.casefold() or ("interface" in normalized and ("received" in normalized or "incoming" in normalized)):
            category = "network_in"
        elif "net.if.out" in key.casefold() or ("interface" in normalized and ("sent" in normalized or "outgoing" in normalized)):
            category = "network_out"
        else:
            category = "other"

        raw_value = item.get("lastvalue")
        try:
            numeric_value = float(raw_value) if raw_value not in (None, "") else None
        except (TypeError, ValueError):
            numeric_value = None

        return {
            "item_id": str(item.get("itemid") or ""),
            "name": name,
            "key": key,
            "category": category,
            "value": str(raw_value) if raw_value is not None else None,
            "numeric_value": numeric_value,
            "units": item.get("units") or "",
            "last_clock": int(item.get("lastclock") or 0),
            "value_type": str(item.get("value_type") or ""),
            "source": "zabbix",
        }

    async def get_latest_metrics(self, host_id: str, limit: int = 200) -> dict[str, Any]:
        safe_limit = max(1, min(int(limit), 500))
        result = await self._call(
            "item.get",
            {
                "output": [
                    "itemid", "name", "key_", "lastvalue",
                    "lastclock", "units", "value_type",
                ],
                "hostids": [str(host_id)],
                "monitored": True,
                "filter": {"status": "0"},
                "sortfield": "name",
                "sortorder": "ASC",
                "limit": safe_limit,
            },
        )
        metrics = [self.normalize_item(item) for item in result or []]
        summary = {
            category: [item for item in metrics if item["category"] == category]
            for category in ("cpu", "memory", "disk", "network_in", "network_out")
        }
        return {
            "host_id": str(host_id),
            "count": len(metrics),
            "metrics": metrics,
            "summary": summary,
            "source": "zabbix",
        }
