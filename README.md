# InfraVision NOC

**Infrastructure observability, inventory correlation, and datacenter visualization.**

InfraVision NOC is an open-source NOC platform that brings infrastructure inventory and operational monitoring into one workspace. It is designed to correlate NetBox assets with Zabbix telemetry and present operational context through Grafana and a dedicated web interface.

> Current status: v0.6.0. NetBox and Zabbix read-only adapters are connected through a correlation service that matches devices by exact hostname first, then normalized management IP. Rack views read live rack records and device placement from NetBox when configured. Grafana now provisions the Zabbix app, token-backed data source, and a reusable NOC dashboard with host-group and host filters. Live Grafana telemetry requires the Zabbix API endpoint and a read-only token in `.env`; the network topology remains a demonstration until interface and cable relationships are synchronized.

## Platform architecture

- **NetBox** — source of truth for sites, racks, devices, interfaces, IP addresses, and tenants.
- **Zabbix** — availability, telemetry, triggers, and operational events.
- **Grafana** — time-series dashboards and operational visualization.
- **FastAPI** — integration layer, normalization, health endpoints, and correlation services.
- **React + TypeScript** — NOC workspace and interactive infrastructure views.
- **PostgreSQL** — application persistence and service databases.
- **Docker Compose** — reproducible local environment.

## Planned capabilities

- Executive NOC overview with availability and incident KPIs.
- Device inventory correlated by exact hostname and normalized management IP, with ambiguous matches isolated for operator review.
- Rack elevations with live NetBox rack selection, front/rear views, rack-unit placement, and a labeled demo fallback.
- Device detail pages with CPU, memory, storage, network, and sensor telemetry.
- Network topology and relationship visualization.
- Incident triage with severity, acknowledgement, and tenant filters.
- Multi-tenant inventory boundaries.
- Audit history and integration synchronization status.

## Repository layout

```text
backend/          FastAPI application and integration adapters
frontend/         React + TypeScript dashboard
infrastructure/   Docker and database configuration
grafana/          Grafana provisioning and NOC dashboards
docs/             Architecture and implementation notes
tests/            Automated tests
docker-compose.yml
```

## Quick start

Requirements: Docker Desktop with the Linux engine running, Docker Compose v2, and Node.js only if running the frontend outside Docker.

1. Copy `.env.example` to `.env` and change the development secrets.
2. Start the platform:

   ```bash
   docker compose up --build -d
   ```

3. Open:
   - Web dashboard: http://localhost:5173
   - API docs: http://localhost:8000/docs
   - Grafana: http://localhost:3000

NetBox and Zabbix are connected as external services through read-only API adapters. Configure `NETBOX_URL`, `NETBOX_TOKEN`, `ZABBIX_URL`, and `ZABBIX_TOKEN` in `.env`. For Grafana, also configure `ZABBIX_GRAFANA_URL` with the full `api_jsonrpc.php` endpoint and `ZABBIX_GRAFANA_TOKEN`. Grafana installs and enables the Zabbix app and provisions the dashboard automatically. API and connector details are documented in [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md). Do not expose these development services directly to the public internet.

## Development

Backend:

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Security notes

- Never commit real API tokens, passwords, customer data, or production inventory.
- Use `.env` for local secrets; only commit `.env.example`.
- Demonstration data is fictional.
- Authentication, authorization, tenant isolation, and production hardening are required before deployment.

## Roadmap

- [x] Project structure and initial NOC dashboard foundation
- [x] FastAPI health and demonstration endpoints
- [x] NetBox read-only API adapter and normalized device inventory endpoint
- [x] Zabbix JSON-RPC adapter for hosts and active triggers
- [x] NetBox-to-Zabbix device correlation endpoint (hostname/IP matching, ambiguity reporting)
- [x] Grafana Zabbix app installation and enablement through provisioning
- [x] Token-backed Zabbix data source provisioning
- [x] NOC Grafana dashboard with group/host variables, problems, CPU, memory, and network panels
- [x] Demonstration rack elevation with front/rear selection and device drill-down
- [x] Demonstration network topology and incident center screens
- [x] Live NetBox rack listing, device assignment, and rack-unit placement
- [ ] Live topology relationships from NetBox interfaces and cables
- [ ] Tenant-aware access control
- [x] API, inventory, rack normalization, integration, correlation, and Grafana provisioning tests (28 tests passing)

## License

MIT. See [LICENSE](LICENSE).
