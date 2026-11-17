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
            # Avoid returning request details or credentials to API consumers.
            message = payload["error"].get("message", "Zabbix API request failed")
            data = payload["error"].get("data", "")
            raise RuntimeError(f"{message}: {data}".strip(": "))
        return payload.get("result")

    async def health(self) -> dict[str, Any]:
        if not self.configured:
            return {"configured": False, "reachable": False, "message": "URL or token not configured"}
        try:
            await self._call("apiinfo.version", {})
            return {"configured": True, "reachable": True, "message": "Zabbix API reachable"}
        except (httpx.HTTPError, RuntimeError, ValueError):
            return {"configured": True, "reachable": False, "message": "Zabbix API unavailable or authentication failed"}

    async def get_hosts(self) -> list[dict[str, Any]]:
        result = await self._call(
            "host.get",
            {
                "output": ["hostid", "host", "name", "status"],
                "selectInterfaces": ["ip", "dns", "main", "type"],
                "sortfield": "host",
            },
        )
        return [
            {
                "external_id": host.get("hostid"),
                "technical_name": host.get("host"),
                "name": host.get("name"),
                "status": "enabled" if host.get("status") == "0" else "disabled",
                "interfaces": host.get("interfaces", []),
                "source": "zabbix",
            }
            for host in result or []
        ]

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
                "external_id": trigger.get("triggerid"),
                "title": trigger.get("description"),
                "priority": trigger.get("priority"),
                "last_change": trigger.get("lastchange"),
                "hosts": trigger.get("hosts", []),
                "source": "zabbix",
            }
            for trigger in result or []
        ]
