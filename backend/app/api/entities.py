from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.auth import Actor, accessible_matter_ids, get_actor, require_matter_access
from app.database import get_db
from app.models.entity import Entity
from app.models.entity_mention import EntityMention
from app.models.relationship import Relationship
from app.models.schemas import EntityDetail, EntityMentionRead, EntitySummary, RelationshipSummary

router = APIRouter()


@router.get("", response_model=list[EntitySummary])
def list_entities(
    db: Session = Depends(get_db),
    matter_id: int | None = None,
    entity_type: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    actor: Actor = Depends(get_actor),
) -> list[EntitySummary]:
    require_matter_access(db, actor, matter_id)
    matter_ids = accessible_matter_ids(db, actor)
    mention_counts = (
        select(EntityMention.entity_id, func.count(EntityMention.id).label("mention_count"))
        .group_by(EntityMention.entity_id)
        .subquery()
    )
    statement = (
        select(Entity, func.coalesce(mention_counts.c.mention_count, 0))
        .outerjoin(mention_counts, mention_counts.c.entity_id == Entity.id)
    )
    if matter_id is not None:
        statement = statement.where(Entity.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(Entity.matter_id.in_(matter_ids))
    if entity_type is not None:
        statement = statement.where(Entity.entity_type == entity_type)
    if q is not None:
        statement = statement.where(Entity.normalized_name.contains(q.lower()))
    statement = statement.order_by(func.coalesce(mention_counts.c.mention_count, 0).desc(), Entity.name).limit(limit).offset(offset)

    return [
        EntitySummary(
            id=entity.id,
            matter_id=entity.matter_id,
            name=entity.name,
            entity_type=entity.entity_type,
            normalized_name=entity.normalized_name,
            mention_count=mention_count,
        )
        for entity, mention_count in db.execute(statement).all()
    ]


@router.get("/{entity_id}", response_model=EntityDetail)
def get_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> EntityDetail:
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    require_matter_access(db, actor, entity.matter_id)

    mentions = list(
        db.scalars(
            select(EntityMention)
            .where(EntityMention.entity_id == entity.id)
            .order_by(EntityMention.document_id, EntityMention.char_start)
        )
    )
    return EntityDetail(
        id=entity.id,
        matter_id=entity.matter_id,
        name=entity.name,
        entity_type=entity.entity_type,
        normalized_name=entity.normalized_name,
        mention_count=len(mentions),
        mentions=[EntityMentionRead.model_validate(mention) for mention in mentions],
    )


@router.get("/{entity_id}/relationships", response_model=list[RelationshipSummary])
def list_entity_relationships(
    entity_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(get_actor),
) -> list[RelationshipSummary]:
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    require_matter_access(db, actor, entity.matter_id)

    statement = (
        select(Relationship)
        .where(or_(Relationship.source_entity_id == entity_id, Relationship.target_entity_id == entity_id))
        .order_by(Relationship.confidence.desc(), Relationship.id)
    )
    relationships = list(db.scalars(statement))

    summaries = []
    for relationship in relationships:
        source_entity = db.get(Entity, relationship.source_entity_id)
        target_entity = db.get(Entity, relationship.target_entity_id)
        summaries.append(
            RelationshipSummary(
                id=relationship.id,
                matter_id=relationship.matter_id,
                source_entity_id=relationship.source_entity_id,
                source_entity_name=source_entity.name if source_entity else "",
                relationship_type=relationship.relationship_type,
                target_entity_id=relationship.target_entity_id,
                target_entity_name=target_entity.name if target_entity else "",
                document_id=relationship.document_id,
                confidence=relationship.confidence,
                evidence=relationship.evidence,
            )
        )
    return summaries
