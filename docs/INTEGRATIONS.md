# Integrations

InfraVision uses read-only API access for inventory and monitoring synchronization.

## NetBox

Configure `NETBOX_URL` and `NETBOX_TOKEN` in the local `.env` file. The adapter supports legacy v1 tokens (`Authorization: Token`) and v2 tokens (`Authorization: Bearer`). Prefer a v2 token with read-only permissions.

The adapter reads:
- `/api/dcim/devices/` — device inventory.
- `/api/dcim/racks/` — rack inventory and rack dimensions.
- `/api/dcim/devices/?rack_id=<id>` — devices mounted in a rack, ordered by position.

The API root and interactive schema are available on a running NetBox instance under `/api/` and `/api/schema/swagger-ui/`. InfraVision correlates device names with Zabbix technical/display hostnames first, then compares normalized primary management IPs with Zabbix interface IP/DNS values. Ambiguous matches are surfaced separately and are never auto-merged.

## Zabbix

Configure `ZABBIX_URL` and `ZABBIX_TOKEN`. The URL may be the Zabbix frontend base path or the full `api_jsonrpc.php` endpoint. The adapter uses JSON-RPC methods `apiinfo.version`, `host.get`, and `trigger.get`, with the API token in the Authorization: Bearer header.

Create a dedicated read-only service account/token in Zabbix. Avoid using an administrator token.

## API endpoints

- `GET /api/integrations/status` — configured and reachable state for both providers.
- `GET /api/inventory/devices` — normalized NetBox device inventory.
- `GET /api/inventory/racks` — normalized NetBox rack inventory.
- `GET /api/inventory/racks/{rack_id}/devices` — devices assigned to a NetBox rack.
- `GET /api/topology/connections` — device nodes and direct interface-to-interface cable links normalized from NetBox cable terminations.
- `GET /api/monitoring/hosts` — normalized Zabbix hosts.
- `GET /api/monitoring/triggers` — currently active Zabbix triggers.
- `GET /api/correlation/devices` — NetBox devices correlated with Zabbix hosts by exact hostname, then normalized management IP. Ambiguous candidates are not automatically merged.
- `GET /api/correlation/inventory` — correlate NetBox devices to Zabbix hosts by exact hostname, then management IP. Ambiguous matches are explicitly reported.

When an integration is not configured, its endpoint returns an empty result set marked as demo mode. It does not fabricate live inventory.

## Security

- Keep credentials only in `.env`.
- Never commit tokens or production configuration.
- Grant the narrowest read permissions available.
- Keep integration traffic on trusted networks or use TLS.
- Do not expose the API publicly until authentication, authorization, and tenant isolation are implemented.


## Grafana and Zabbix data source

The Grafana container automatically installs and enables the Zabbix app plugin. Provisioning files are stored under `grafana/provisioning/`, and the dashboard JSON is stored under `grafana/dashboards/`.

Configure two additional variables in the project-root `.env` file:

- `ZABBIX_GRAFANA_URL` — the full Zabbix API endpoint, including `api_jsonrpc.php`, for example `https://zabbix.example.com/api_jsonrpc.php`.
- `ZABBIX_GRAFANA_TOKEN` — an API token belonging to a read-only Zabbix service account.

The Grafana connector uses its own endpoint and token because the Grafana container must be able to reach the Zabbix API from its network. These variables are separate from `ZABBIX_URL` and `ZABBIX_TOKEN`, which are used by the FastAPI adapter.

The token is provisioned under Grafana's `secureJsonData.apiToken` field, so Grafana encrypts it in its data-source configuration. Do not put the token in dashboard JSON or commit it to Git.

The provisioned dashboard is named **InfraVision NOC - Zabbix Monitoring**. It includes host-group and host variables, an active-problem queue, and time-series panels for CPU, memory, and network traffic. Metric panels use item-name regular expressions; actual values depend on the item names and templates configured on the connected Zabbix server.

Grafana's Zabbix app requires Grafana 11.6.0 or later and must be both installed and enabled before its data source can be used. InfraVision pins Grafana 11.6.0 in Docker Compose and provisions the app and data source at startup.


## NetBox cable topology

The topology adapter reads `/api/dcim/cables/` and builds a device graph from direct `dcim.interface` terminations. The nested termination object supplies the interface and its owning device, so the graph does not need to infer device relationships from names or IP addresses.

Each graph node represents a NetBox device. Each edge represents a direct cable between device interfaces and includes the two interface names, cable ID, label, type, status, and optional length.

The endpoint currently retrieves up to 500 cable records per request. The response includes `has_more` when NetBox reports additional records and `unsupported_cable_count` for cables whose ends are not both direct device interfaces. Cables terminating on patch panels, front ports, rear ports, or pass-through ports are not traced end-to-end yet; those relationships are deliberately excluded rather than guessed.

If NetBox is not configured, the endpoint returns an empty `demo=true` graph. The frontend uses a clearly labeled fictional sample topology only in that demo mode. If NetBox is configured but has no direct device-interface links, the UI displays an empty live result instead of substituting sample data.


## Zabbix host latest metrics

- `GET /api/monitoring/hosts/{host_id}/metrics` — retrieves enabled, monitored Zabbix items for one host using `item.get`, including the latest value, units, item key, and last update timestamp.
- Values are grouped into best-effort categories (CPU, memory, disk, network received, and network sent) using item keys and names. Items that do not match these known patterns remain available under the `other` category.
- The endpoint does not invent data: an unconfigured Zabbix integration returns an empty result marked as demo mode. A configured host with no enabled monitored items returns an empty live result.
- The inventory view fetches latest metrics only after the operator selects a uniquely correlated NetBox device. Ambiguous hostname/IP matches are shown for review; no telemetry is silently attached to an ambiguous asset.



## Zabbix monitoring overlay on topology

The combined endpoint is `GET /api/topology/monitoring`. It loads physical devices and direct interface-to-interface cable links from NetBox, then enriches each node with a Zabbix host match and current host availability.

The Zabbix adapter requests host interfaces through `host.get`. Interface availability values are normalized as `0 = unknown`, `1 = available`, and `2 = unavailable`. A host with mixed available and unavailable interfaces is labeled partially available; disabled hosts remain disabled, and hosts without a usable availability signal remain unknown.

Host association reuses the inventory correlation policy: exact device name against Zabbix technical/display hostname first, then normalized NetBox primary management IP against Zabbix interface IP. One-to-many and many-to-one matches are marked ambiguous; they do not receive a selected Zabbix host or an inferred health state.

Active Zabbix triggers are loaded with `trigger.get` and grouped by host. The node inspector reports total active triggers and separates priorities 4–5 as critical and 2–3 as warnings. Trigger counts are only attached to a uniquely matched host.

If Zabbix is not configured or the API is unavailable, NetBox physical topology remains visible and monitoring fields explicitly indicate not configured or unavailable. This is not demo telemetry. When NetBox itself is not configured, the endpoint returns an empty demo result and the frontend uses its clearly labeled fictional sample topology.
