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
