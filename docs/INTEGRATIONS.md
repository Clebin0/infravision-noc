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
