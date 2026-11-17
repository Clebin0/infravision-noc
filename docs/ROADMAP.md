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
- [ ] Item value normalization and history/trend retrieval
- [ ] Incident lifecycle and severity mapping

## Milestone 4 — Visualization
- [ ] Grafana provisioning
- [ ] Device telemetry panels
- [x] Demonstration network topology page
- [x] Rack drill-down to a device details panel
- [ ] Live topology links from NetBox interfaces and cables

## Milestone 5 — Production readiness
- [ ] Authentication and RBAC
- [ ] Tenant isolation tests
- [ ] Audit log
- [x] GitHub Actions CI workflow and API/integration tests
- [ ] Live integration contract tests
- [ ] Backup, observability, and deployment documentation
