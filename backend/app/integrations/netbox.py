from typing import Any

import httpx


class NetBoxClient:
    """Read-only NetBox REST client. Supports v1 and v2 API token headers."""

    def __init__(self, base_url: str | None, token: str | None, timeout: float = 10.0):
        self.base_url = (base_url or "").rstrip("/")
        self.token = token or ""
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.token)

    def _headers(self) -> dict[str, str]:
        # NetBox v2 tokens use Bearer; legacy v1 tokens use Token.
        scheme = "Bearer" if self.token.startswith("nbt_") else "Token"
        return {
            "Authorization": f"{scheme} {self.token}",
            "Accept": "application/json",
        }

    async def _get_list(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.configured:
            return {"count": 0, "results": []}

        query = dict(params or {})
        query["limit"] = max(1, min(int(query.get("limit", 100)), 500))
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/{path.lstrip('/')}",
                headers=self._headers(),
                params=query,
            )
            response.raise_for_status()
            payload = response.json()

        results = payload.get("results", [])
        return {
            "count": payload.get("count", len(results)),
            "results": results,
            "has_more": bool(payload.get("next")),
        }

    async def health(self) -> dict[str, Any]:
        if not self.configured:
            return {"configured": False, "reachable": False, "message": "URL or token not configured"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/", headers=self._headers())
                response.raise_for_status()
            return {"configured": True, "reachable": True, "message": "NetBox API reachable"}
        except (httpx.HTTPError, ValueError):
            return {"configured": True, "reachable": False, "message": "NetBox API unavailable or authentication failed"}

    async def get_devices(self, limit: int = 100) -> dict[str, Any]:
        payload = await self._get_list("dcim/devices/", {"limit": limit})
        return {
            "configured": self.configured,
            "count": payload["count"],
            "has_more": payload["has_more"],
            "results": [self.normalize_device(item) for item in payload["results"]],
        }

    async def get_racks(self, limit: int = 200) -> dict[str, Any]:
        payload = await self._get_list("dcim/racks/", {"limit": limit})
        return {
            "configured": self.configured,
            "count": payload["count"],
            "has_more": payload["has_more"],
            "results": [self.normalize_rack(item) for item in payload["results"]],
        }

    async def get_rack_devices(self, rack_id: int, limit: int = 200) -> dict[str, Any]:
        payload = await self._get_list(
            "dcim/devices/",
            {"rack_id": rack_id, "limit": limit, "ordering": "position"},
        )
        return {
            "configured": self.configured,
            "count": payload["count"],
            "has_more": payload["has_more"],
            "results": [self.normalize_device(item) for item in payload["results"]],
        }

    @staticmethod
    def normalize_rack(item: dict[str, Any]) -> dict[str, Any]:
        def display(value: Any) -> Any:
            if isinstance(value, dict):
                return value.get("display") or value.get("name") or value.get("value")
            return value

        return {
            "external_id": str(item.get("id", "")),
            "name": item.get("name") or item.get("display") or "Unnamed rack",
            "site": display(item.get("site")),
            "tenant": display(item.get("tenant")),
            "rack_group": display(item.get("group")),
            "status": display(item.get("status")),
            "facility": item.get("facility"),
            "u_height": item.get("u_height"),
            "width": item.get("width"),
            "source": "netbox",
        }

    @staticmethod
    def normalize_device(item: dict[str, Any]) -> dict[str, Any]:
        def display(value: Any) -> Any:
            if isinstance(value, dict):
                return value.get("display") or value.get("name") or value.get("value") or value.get("address")
            return value

        primary_ip = item.get("primary_ip4") or item.get("primary_ip")
        rack = item.get("rack")
        return {
            "external_id": str(item.get("id", "")),
            "name": item.get("name") or item.get("display") or "Unnamed device",
            "status": display(item.get("status")),
            "device_type": display(item.get("device_type")),
            "role": display(item.get("role")),
            "site": display(item.get("site")),
            "tenant": display(item.get("tenant")),
            "rack": display(rack),
            "rack_id": rack.get("id") if isinstance(rack, dict) else None,
            "device_height": (item.get("device_type") or {}).get("u_height") if isinstance(item.get("device_type"), dict) else None,
            "position": item.get("position"),
            "face": item.get("face"),
            "primary_ip": display(primary_ip),
            "source": "netbox",
        }
