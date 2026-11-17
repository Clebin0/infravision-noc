# Roadmap

## Milestone 1 — Foundation
- [x] Repository structure
- [x] FastAPI health and overview endpoints
- [x] React NOC dashboard shell
- [x] Docker Compose foundation
- [x] Local frontend build and API checks

## Milestone 2 — Inventory
- [x] NetBox configuration and read-only API client
- [x] Initial device normalization and inventory endpoint
- [ ] Sites, tenants, interfaces, and richer inventory synchronization
- [x] Device identity correlation by exact hostname and normalized management IP
- [x] Ambiguous matches surfaced for operator review
- [x] Rack front/rear elevation, device detail panel, and NetBox live inventory fallback
- [x] Live NetBox rack listing, device assignment, and rack-unit placement (unknown device height falls back to 1U)

## Milestone 3 — Monitoring
- [x] Zabbix JSON-RPC API client
- [x] Host and active trigger retrieval endpoints
- [x] Latest monitored item retrieval and best-effort CPU, memory, disk, and network categorization
- [ ] Historical item values and trend retrieval
- [ ] Incident lifecycle and severity mapping

## Milestone 4 — Visualization
- [x] Grafana Zabbix app installation and enablement provisioning
- [x] Token-backed Zabbix data source provisioning
- [x] Device telemetry panels for CPU, memory and network traffic, plus problem queue
- [x] Demonstration network topology page
- [x] Rack drill-down to a device details panel
- [x] Live topology nodes and direct interface-to-interface links from NetBox cable terminations
- [ ] End-to-end tracing through patch panels and pass-through ports
- [x] Zabbix host availability and active-problem overlays on topology nodes, with ambiguous matches kept unassigned
- [ ] Per-interface telemetry and health overlays on topology links

## Milestone 5 — Production readiness
- [ ] Authentication and RBAC
- [ ] Tenant isolation tests
- [ ] Audit log
- [x] GitHub Actions CI workflow and API/integration tests
- [ ] Live integration contract tests
- [ ] Backup, observability, and deployment documentation
