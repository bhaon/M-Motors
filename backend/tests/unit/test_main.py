"""Tests sur l'application FastAPI (health)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_ok(client: TestClient) -> None:
    """GET /api/health renvoie le statut et la version."""
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.APP_VERSION
