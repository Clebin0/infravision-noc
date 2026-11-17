# Roadmap

## Milestone 1 — Foundation
- [x] Repository structure
- [x] FastAPI health and overview endpoints
- [x] React NOC dashboard shell
- [x] Docker Compose foundation
- [ ] Local build verification

## Milestone 2 — Inventory
- [x] NetBox configuration and read-only API client
- [x] Initial device normalization and inventory endpoint
- [ ] Sites, tenants, interfaces, and richer inventory synchronization
- [ ] Device identity mapping and Zabbix host correlation
- [ ] Rack front/rear elevation

## Milestone 3 — Monitoring
- [x] Zabbix JSON-RPC API client
- [x] Host and active trigger retrieval endpoints
- [ ] Item value normalization and history/trend retrieval
- [ ] Incident lifecycle and severity mapping

## Milestone 4 — Visualization
- [ ] Grafana provisioning
- [ ] Device telemetry panels
- [ ] Network topology
- [ ] Drill-down from rack to device to metrics

## Milestone 5 — Production readiness
- [ ] Authentication and RBAC
- [ ] Tenant isolation tests
- [ ] Audit log
- [ ] Integration tests and CI
- [ ] Backup, observability, and deployment documentation
