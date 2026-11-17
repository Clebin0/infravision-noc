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
        if not self.configured:
            return {"configured": False, "results": [], "count": 0}
        params = {"limit": max(1, min(limit, 500))}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/dcim/devices/",
                headers=self._headers(),
                params=params,
            )
            response.raise_for_status()
            payload = response.json()

        results = payload.get("results", [])
        return {
            "configured": True,
            "count": payload.get("count", len(results)),
            "results": [self.normalize_device(item) for item in results],
        }

    @staticmethod
    def normalize_device(item: dict[str, Any]) -> dict[str, Any]:
        def display(value: Any) -> Any:
            if isinstance(value, dict):
                return value.get("display") or value.get("name") or value.get("value") or value.get("address")
            return value

        primary_ip = item.get("primary_ip4") or item.get("primary_ip")
        return {
            "external_id": str(item.get("id", "")),
            "name": item.get("name") or item.get("display") or "Unnamed device",
            "status": display(item.get("status")),
            "device_type": display(item.get("device_type")),
            "role": display(item.get("role")),
            "site": display(item.get("site")),
            "tenant": display(item.get("tenant")),
            "rack": display(item.get("rack")),
            "position": item.get("position"),
            "face": item.get("face"),
            "primary_ip": display(primary_ip),
            "source": "netbox",
        }
