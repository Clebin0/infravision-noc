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

    async def get_topology(self, limit: int = 500) -> dict[str, Any]:
        payload = await self._get_list("dcim/cables/", {"limit": limit})
        normalized = self.normalize_topology(payload["results"])
        return {
            **normalized,
            "configured": self.configured,
            "cable_count": payload["count"],
            "returned_cable_count": len(payload["results"]),
            "has_more": payload["has_more"],
        }

    @staticmethod
    def normalize_topology(cables: list[dict[str, Any]]) -> dict[str, Any]:
        """Build device nodes and interface links from NetBox direct cable terminations.

        Only direct device-interface to device-interface cable connections are
        represented. Cables terminating at patch-panel/pass-through ports are
        counted separately until NetBox cable-path tracing is implemented.
        """
        def display(value: Any) -> Any:
            if isinstance(value, dict):
                return value.get("display") or value.get("name") or value.get("label") or value.get("value") or value.get("address")
            return value

        def normalize_endpoint(termination: dict[str, Any]) -> dict[str, Any] | None:
            if termination.get("object_type") != "dcim.interface":
                return None

            interface = termination.get("object") or {}
            device = interface.get("device") or {}
            primary_ip = device.get("primary_ip4") or device.get("primary_ip")
            device_id = device.get("id")
            if not device_id:
                return None

            interface_id = termination.get("object_id") or interface.get("id")
            if not interface_id:
                return None

            return {
                "interface_id": str(interface_id),
                "interface_name": interface.get("name") or interface.get("display") or "Unnamed interface",
                "interface_label": interface.get("label") or "",
                "interface_type": display(interface.get("type")),
                "enabled": interface.get("enabled"),
                "device_id": str(device_id),
                "device_name": device.get("name") or device.get("display_name") or device.get("display") or "Unnamed device",
                "device_type": display(device.get("device_type")),
                "role": display(device.get("role")),
                "site": display(device.get("site")),
                "device_status": display(device.get("status")),
                "primary_ip": display(primary_ip),
            }

        nodes: dict[str, dict[str, Any]] = {}
        links: list[dict[str, Any]] = []
        unsupported_cables = 0

        for cable in cables:
            a_endpoints = [
                endpoint
                for termination in cable.get("a_terminations") or []
                if (endpoint := normalize_endpoint(termination)) is not None
            ]
            b_endpoints = [
                endpoint
                for termination in cable.get("b_terminations") or []
                if (endpoint := normalize_endpoint(termination)) is not None
            ]

            if not a_endpoints or not b_endpoints:
                unsupported_cables += 1
                continue

            cable_id = str(cable.get("id", ""))
            link_index = 0
            for endpoint_a in a_endpoints:
                for endpoint_b in b_endpoints:
                    link_index += 1
                    links.append({
                        "id": f"{cable_id}:{link_index}",
                        "cable_id": cable_id,
                        "label": cable.get("label") or cable.get("display") or f"Cable {cable_id}",
                        "status": display(cable.get("status")),
                        "type": display(cable.get("type")),
                        "color": cable.get("color"),
                        "length": cable.get("length"),
                        "length_unit": display(cable.get("length_unit")),
                        "a": endpoint_a,
                        "b": endpoint_b,
                    })

                    for endpoint in (endpoint_a, endpoint_b):
                        device_id = endpoint["device_id"]
                        node = nodes.setdefault(device_id, {
                            "id": device_id,
                            "name": endpoint["device_name"],
                            "device_type": endpoint["device_type"],
                            "role": endpoint["role"],
                            "site": endpoint["site"],
                            "asset_status": endpoint["device_status"],
                            "primary_ip": endpoint["primary_ip"],
                            "interfaces": {},
                        })
                        node["interfaces"][endpoint["interface_id"]] = {
                            "id": endpoint["interface_id"],
                            "name": endpoint["interface_name"],
                            "label": endpoint["interface_label"],
                            "type": endpoint["interface_type"],
                            "enabled": endpoint["enabled"],
                        }

        normalized_nodes = []
        for node in nodes.values():
            interfaces = list(node.pop("interfaces").values())
            normalized_nodes.append({
                **node,
                "interface_count": len(interfaces),
                "interfaces": sorted(interfaces, key=lambda item: item["name"]),
            })

        normalized_nodes.sort(key=lambda item: item["name"].casefold())
        links.sort(key=lambda item: (item["a"]["device_name"].casefold(), item["b"]["device_name"].casefold(), item["id"]))

        return {
            "nodes": normalized_nodes,
            "links": links,
            "connection_count": len(links),
            "device_count": len(normalized_nodes),
            "unsupported_cable_count": unsupported_cables,
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
