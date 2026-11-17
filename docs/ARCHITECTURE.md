# Architecture

## Design principles

1. NetBox is the source of truth for inventory and physical placement.
2. Zabbix is the source of truth for operational telemetry and trigger state.
3. InfraVision owns correlation, presentation, and workflow metadata; it should not duplicate upstream inventory unnecessarily.
4. Grafana remains responsible for time-series exploration and dashboards.
5. All integration adapters must tolerate timeouts, rate limits, partial data, and upstream unavailability.

## Correlation strategy

Use a stable external identifier wherever possible. NetBox device IDs and Zabbix host IDs are stored as external references. Hostname and management IP are fallback matching signals, not primary keys. Ambiguous matches must be surfaced for operator review rather than silently merged.

## Initial service boundaries

- API: overview, devices, incidents, rack views, integration health.
- NetBox adapter: sites, tenants, racks, devices, interfaces, IP addresses.
- Zabbix adapter: hosts, item values, triggers, events.
- Grafana adapter: datasource and dashboard links/provisioning.
- Frontend: NOC overview, inventory, rack elevation, topology, incident queue.

## Security

Secrets are environment-only. Integrations use least-privilege service accounts. Tenant filtering must be enforced server-side. Demo mode must be visibly distinguished from live telemetry.
