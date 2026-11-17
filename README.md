# InfraVision NOC

**Infrastructure observability, inventory correlation, and datacenter visualization.**

InfraVision NOC is an open-source NOC platform that brings infrastructure inventory and operational monitoring into one workspace. It is designed to correlate NetBox assets with Zabbix telemetry and present operational context through Grafana and a dedicated web interface.

> Current status: foundation scaffold. The dashboard currently uses clearly labeled demonstration data while service integrations are implemented incrementally.

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
- Device inventory correlated by stable identifiers.
- Rack elevations with front/rear views and rack-unit placement.
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
dashboards/       Grafana dashboard provisioning
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

The initial compose profile starts the application foundation. NetBox and Zabbix services will be added with their dedicated configuration in the integration milestone. Do not expose these development services directly to the public internet.

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
- [ ] NetBox API adapter and inventory synchronization
- [ ] Zabbix API adapter and host/trigger correlation
- [ ] Grafana provisioning and embedded dashboard links
- [ ] Rack elevation and network topology views
- [ ] Tenant-aware access control
- [ ] Integration and end-to-end tests

## License

MIT. See [LICENSE](LICENSE).
