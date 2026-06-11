from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
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
) -> KnowledgeGraphResponse:
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
) -> KnowledgeGraphResponse:
    if depth < 1 or depth > 4:
        raise HTTPException(status_code=400, detail="depth must be between 1 and 4")
    try:
        return build_neighborhood(
            db,
            entity_id=entity_id,
            depth=depth,
            relationship_type=relationship_type,
            min_confidence=min_confidence,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/path", response_model=GraphPathResponse)
def get_shortest_paths(
    source_entity_id: int,
    target_entity_id: int,
    db: Session = Depends(get_db),
    max_depth: int = 4,
) -> GraphPathResponse:
    if max_depth < 1 or max_depth > 8:
        raise HTTPException(status_code=400, detail="max_depth must be between 1 and 8")
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
) -> GraphMetrics:
    return build_knowledge_graph(db, matter_id=matter_id, min_confidence=min_confidence).metrics
