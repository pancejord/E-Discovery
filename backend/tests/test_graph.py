from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
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

    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_knowledge_graph_endpoints_return_visualization_data(client: TestClient) -> None:
    document_text = (
        "Jane Smith met with Acme Corp in New York on March 3, 2024. "
        "John Doe discussed Rule 26 with Jane Smith and Acme Corp."
    )
    upload_response = client.post(
        "/documents/upload",
        files={"file": ("graph.txt", document_text.encode("utf-8"), "text/plain")},
    )
    assert upload_response.status_code == 200

    graph_response = client.get("/api/graph")
    assert graph_response.status_code == 200
    graph = graph_response.json()
    assert graph["metrics"]["node_count"] >= 5
    assert graph["metrics"]["edge_count"] > 0
    assert graph["metrics"]["connected_component_count"] == 1
    assert graph["metrics"]["top_entities"]

    node_labels = {node["label"] for node in graph["nodes"]}
    assert {"Jane Smith", "Acme Corp", "John Doe"} <= node_labels
    assert any(edge["relationship_type"] == "mentioned_with" for edge in graph["edges"])

    acme = next(node for node in graph["nodes"] if node["label"] == "Acme Corp")
    jane = next(node for node in graph["nodes"] if node["label"] == "Jane Smith")

    neighborhood_response = client.get(f"/api/graph/neighborhood/{acme['id']}", params={"depth": 1})
    assert neighborhood_response.status_code == 200
    neighborhood = neighborhood_response.json()
    assert any(node["id"] == acme["id"] for node in neighborhood["nodes"])
    assert neighborhood["metrics"]["edge_count"] > 0

    path_response = client.get(
        "/api/graph/path",
        params={"source_entity_id": acme["id"], "target_entity_id": jane["id"], "max_depth": 2},
    )
    assert path_response.status_code == 200
    paths = path_response.json()["paths"]
    assert paths
    assert paths[0][0]["id"] == acme["id"]
    assert paths[0][-1]["id"] == jane["id"]

    metrics_response = client.get("/api/graph/metrics")
    assert metrics_response.status_code == 200
    assert metrics_response.json()["node_count"] == graph["metrics"]["node_count"]


def test_graph_rejects_invalid_depth(client: TestClient) -> None:
    response = client.get("/api/graph/neighborhood/1", params={"depth": 0})

    assert response.status_code == 400
    assert response.json()["detail"] == "depth must be between 1 and 4"
