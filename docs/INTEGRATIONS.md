# Integrations

InfraVision uses read-only API access for inventory and monitoring synchronization.

## NetBox

Configure `NETBOX_URL` and `NETBOX_TOKEN` in the local `.env` file. The adapter supports both legacy v1 tokens (Authorization: Token) and v2 tokens (Authorization: Bearer). Prefer a read-only v2 token.

The initial adapter reads devices from `/api/dcim/devices/` and normalizes the fields needed by the NOC inventory view.

## Zabbix

Configure `ZABBIX_URL` and `ZABBIX_TOKEN`. The URL may be the Zabbix frontend base path or the full `api_jsonrpc.php` endpoint. The adapter uses JSON-RPC methods `apiinfo.version`, `host.get`, and `trigger.get`, with the token in the Authorization: Bearer header.

Create a dedicated read-only service account/token in Zabbix. Avoid using an administrator token.

## API endpoints

- `GET /api/integrations/status` — configured and reachable state for both providers.
- `GET /api/inventory/devices` — normalized NetBox device inventory.
- `GET /api/monitoring/hosts` — normalized Zabbix hosts.
- `GET /api/monitoring/triggers` — currently active Zabbix triggers.

When an integration is not configured, the endpoint returns an empty result set marked as demo mode. It does not fabricate live inventory.

## Security

- Keep credentials only in `.env`.
- Never commit tokens or production configuration.
- Grant the narrowest read permissions available.
- Keep integration traffic on trusted networks or use TLS.
- Do not expose the API publicly until authentication, authorization, and tenant isolation are implemented.
