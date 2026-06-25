from fastapi.testclient import TestClient

from app.core.config import settings
from app.database import Base, engine, init_db
from app.main import app


def test_health_check() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_init_db_skips_create_all_in_production(monkeypatch) -> None:
    calls = []

    def fake_create_all(bind):
        calls.append(bind)

    monkeypatch.setattr(settings, "app_environment", "production")
    monkeypatch.setattr(settings, "database_auto_create_tables", True)
    monkeypatch.setattr(Base.metadata, "create_all", fake_create_all)

    init_db()

    assert calls == []


def test_init_db_allows_create_all_for_development(monkeypatch) -> None:
    calls = []

    def fake_create_all(bind):
        calls.append(bind)

    monkeypatch.setattr(settings, "app_environment", "development")
    monkeypatch.setattr(settings, "database_auto_create_tables", True)
    monkeypatch.setattr(Base.metadata, "create_all", fake_create_all)

    init_db()

    assert calls == [engine]
