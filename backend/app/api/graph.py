from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import Actor, get_actor, require_matter_access
from app.database import get_db
from app.models.entity import Entity
from app.models.schemas import GraphMetrics, GraphPathResponse, KnowledgeGraphResponse
from app.services.knowledge_graph import build_knowledge_graph, build_neighborhood, shortest_paths

router = APIRouter()


@router.get("", response_model=KnowledgeGraphResponse)
def get_knowledge_graph(
    db: Session = Depends(get_db),
    matter_id: int | None = None,
    relationship_type: str | None = None,
    min_confidence: float = 0.0,
    entity_limit: int = 250,
    actor: Actor = Depends(get_actor),
) -> KnowledgeGraphResponse:
    require_matter_access(actor, matter_id)
    return build_knowledge_graph(
        db,
        matter_id=matter_id,
        relationship_type=relationship_type,
        min_confidence=min_confidence,
        entity_limit=entity_limit,
    )


@router.get("/neighborhood/{entity_id}", response_model=KnowledgeGraphResponse)
def get_entity_neighborhood(
    entity_id: int,
    db: Session = Depends(get_db),
    depth: int = 1,
    relationship_type: str | None = None,
    min_confidence: float = 0.0,
    actor: Actor = Depends(get_actor),
) -> KnowledgeGraphResponse:
    if depth < 1 or depth > 4:
        raise HTTPException(status_code=400, detail="depth must be between 1 and 4")
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    require_matter_access(actor, entity.matter_id)
    try:
        graph = build_neighborhood(
            db,
            entity_id=entity_id,
            depth=depth,
            relationship_type=relationship_type,
            min_confidence=min_confidence,
        )
        return graph
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/path", response_model=GraphPathResponse)
def get_shortest_paths(
    source_entity_id: int,
    target_entity_id: int,
    db: Session = Depends(get_db),
    max_depth: int = 4,
    actor: Actor = Depends(get_actor),
) -> GraphPathResponse:
    if max_depth < 1 or max_depth > 8:
        raise HTTPException(status_code=400, detail="max_depth must be between 1 and 8")
    source = db.get(Entity, source_entity_id)
    target = db.get(Entity, target_entity_id)
    if source is None or target is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    require_matter_access(actor, source.matter_id)
    require_matter_access(actor, target.matter_id)
    try:
        paths = shortest_paths(
            db,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            max_depth=max_depth,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return GraphPathResponse(
        source_entity_id=source_entity_id,
        target_entity_id=target_entity_id,
        paths=paths,
    )


@router.get("/metrics", response_model=GraphMetrics)
def get_graph_metrics(
    db: Session = Depends(get_db),
    matter_id: int | None = None,
    min_confidence: float = 0.0,
    actor: Actor = Depends(get_actor),
) -> GraphMetrics:
    require_matter_access(actor, matter_id)
    return build_knowledge_graph(db, matter_id=matter_id, min_confidence=min_confidence).metrics
