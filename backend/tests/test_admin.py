from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import hash_api_key
from app.core.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Matter, Role, User


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", None)
    app.dependency_overrides[get_db] = override_get_db

    seed_admin_fixture(testing_session_local)
    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def seed_admin_fixture(testing_session_local: sessionmaker[Session]) -> None:
    db = testing_session_local()
    admin_role = Role(name="admin", is_admin=True)
    reviewer_role = Role(name="reviewer", is_admin=False)
    matter = Matter(name="Admin Matter", matter_number="ADM-1")
    db.add_all([admin_role, reviewer_role, matter])
    db.commit()
    for row in [admin_role, reviewer_role, matter]:
        db.refresh(row)

    db.add_all(
        [
            User(
                email="admin@example.com",
                display_name="Admin",
                api_key_hash=hash_api_key("admin-key"),
                role_id=admin_role.id,
            ),
            User(
                email="reviewer@example.com",
                display_name="Reviewer",
                api_key_hash=hash_api_key("reviewer-key"),
                role_id=reviewer_role.id,
            ),
        ]
    )
    db.commit()
    db.close()


def test_admin_manages_roles_users_keys_and_memberships(client: TestClient) -> None:
    headers = {"X-API-Key": "admin-key"}

    role_response = client.post(
        "/api/admin/roles",
        headers=headers,
        json={"name": "case_manager", "description": "Matter assignment manager", "is_admin": False},
    )
    assert role_response.status_code == 200
    role_id = role_response.json()["id"]

    user_response = client.post(
        "/api/admin/users",
        headers=headers,
        json={"email": "new-reviewer@example.com", "display_name": "New Reviewer", "role_id": role_id},
    )
    assert user_response.status_code == 200
    created = user_response.json()
    assert created["api_key"].startswith("ls_")
    assert created["user"]["email"] == "new-reviewer@example.com"
    user_id = created["user"]["id"]

    users_response = client.get("/api/admin/users", headers=headers)
    assert users_response.status_code == 200
    assert all("api_key" not in user for user in users_response.json())

    update_response = client.patch(
        f"/api/admin/users/{user_id}",
        headers=headers,
        json={"display_name": "Updated Reviewer", "is_active": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["display_name"] == "Updated Reviewer"
    assert update_response.json()["is_active"] is False
    inactive_key_response = client.get("/api/matters", headers={"X-API-Key": created["api_key"]})
    assert inactive_key_response.status_code == 401

    reactivate_response = client.patch(
        f"/api/admin/users/{user_id}",
        headers=headers,
        json={"is_active": True},
    )
    assert reactivate_response.status_code == 200

    rotate_response = client.post(f"/api/admin/users/{user_id}/rotate-key", headers=headers, json={})
    assert rotate_response.status_code == 200
    rotated_key = rotate_response.json()["api_key"]
    assert rotated_key.startswith("ls_")
    old_key_response = client.get("/api/matters", headers={"X-API-Key": created["api_key"]})
    assert old_key_response.status_code == 401
    new_key_response = client.get("/api/matters", headers={"X-API-Key": rotated_key})
    assert new_key_response.status_code == 200

    membership_response = client.post(
        "/api/admin/memberships",
        headers=headers,
        json={"user_id": user_id, "matter_id": 1, "role": "reviewer"},
    )
    assert membership_response.status_code == 200
    membership_id = membership_response.json()["id"]

    update_membership = client.patch(
        f"/api/admin/memberships/{membership_id}",
        headers=headers,
        json={"role": "lead_reviewer"},
    )
    assert update_membership.status_code == 200
    assert update_membership.json()["role"] == "lead_reviewer"

    delete_membership = client.delete(f"/api/admin/memberships/{membership_id}", headers=headers)
    assert delete_membership.status_code == 204

    audit_response = client.get("/api/audit", headers=headers, params={"action": "user.rotate_key"})
    assert audit_response.status_code == 200
    assert audit_response.json()[0]["details"]["user_id"] == user_id


def test_non_admin_cannot_use_admin_endpoints(client: TestClient) -> None:
    response = client.get("/api/admin/users", headers={"X-API-Key": "reviewer-key"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"
