from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as integration_router
from app.settings import settings

app = FastAPI(
    title="InfraVision NOC API",
    description="Infrastructure inventory and observability correlation API.",
    version="0.9.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(integration_router)


@app.get("/api/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "service": "infravision-api",
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/overview", tags=["overview"])
def overview():
    """Fictional seed data for the first dashboard milestone."""
    return {
        "demo": True,
        "kpis": {
            "availability": 99.94,
            "devices_total": 128,
            "devices_online": 124,
            "active_incidents": 3,
            "sites": 4,
        },
        "devices": [
            {"id": "srv-core-01", "name": "core-srv-01", "type": "Server", "site": "São Paulo DC", "status": "online", "cpu": 24, "memory": 68, "ip": "10.10.1.11"},
            {"id": "sw-dist-02", "name": "dist-sw-02", "type": "Switch", "site": "São Paulo DC", "status": "warning", "cpu": 71, "memory": 54, "ip": "10.10.1.22"},
            {"id": "fw-edge-01", "name": "edge-fw-01", "type": "Firewall", "site": "Curitiba POP", "status": "online", "cpu": 18, "memory": 42, "ip": "10.20.0.1"},
            {"id": "nas-backup-01", "name": "backup-nas-01", "type": "Storage", "site": "São Paulo DC", "status": "critical", "cpu": 12, "memory": 81, "ip": "10.10.2.30"},
        ],
        "incidents": [
            {"id": "INC-2048", "severity": "critical", "title": "Storage pool capacity above 90%", "device": "backup-nas-01", "age": "8 min"},
            {"id": "INC-2047", "severity": "warning", "title": "High CPU utilization", "device": "dist-sw-02", "age": "21 min"},
            {"id": "INC-2045", "severity": "warning", "title": "Interface errors detected", "device": "core-srv-01", "age": "46 min"},
        ],
    }
