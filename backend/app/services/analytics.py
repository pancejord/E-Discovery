from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.custodian import Custodian
from app.models.document import Document
from app.models.entity import Entity
from app.models.relationship import Relationship
from app.models.schemas import (
    AnalyticsBucket,
    AnalyticsDashboard,
    AnalyticsSnapshot,
    CommunicationMetric,
    TimelinePoint,
)


def build_analytics_dashboard(
    db: Session,
    matter_id: int | None = None,
    matter_ids: list[int] | None = None,
    custodian_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> AnalyticsDashboard:
    documents = _load_documents(db, matter_id, matter_ids, custodian_id, date_from, date_to)
    document_ids = {document.id for document in documents}
    entities = _load_entities(db, matter_id, matter_ids)
    relationships = _load_relationships(db, matter_id, matter_ids, document_ids)
    custodians = _load_custodians(db)

    file_type_counts = _count_values(document.file_type for document in documents)
    custodian_counts = _custodian_counts(documents, custodians)
    snapshot = AnalyticsSnapshot(
        document_count=len(documents),
        entity_count=len(entities),
        relationship_count=len(relationships),
        file_type_counts=dict(file_type_counts),
        custodian_counts=dict(custodian_counts),
    )

    return AnalyticsDashboard(
        snapshot=snapshot,
        document_timeline=_document_timeline(documents),
        file_type_distribution=_buckets(file_type_counts),
        document_type_distribution=_buckets(
            _count_values(document.document_type or "Unclassified" for document in documents)
        ),
        entity_type_distribution=_buckets(_count_values(entity.entity_type for entity in entities)),
        relationship_type_distribution=_buckets(
            _count_values(relationship.relationship_type for relationship in relationships)
        ),
        top_custodians=_buckets(custodian_counts, limit=10),
        communication_pairs=_communication_pairs(db, relationships),
    )


def _load_documents(
    db: Session,
    matter_id: int | None,
    matter_ids: list[int] | None,
    custodian_id: int | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> list[Document]:
    statement = select(Document)
    if matter_id is not None:
        statement = statement.where(Document.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(Document.matter_id.in_(matter_ids))
    if custodian_id is not None:
        statement = statement.where(Document.custodian_id == custodian_id)
    if date_from is not None:
        statement = statement.where(Document.document_date >= date_from)
    if date_to is not None:
        statement = statement.where(Document.document_date <= date_to)
    return list(db.scalars(statement))


def _load_entities(db: Session, matter_id: int | None, matter_ids: list[int] | None) -> list[Entity]:
    statement = select(Entity)
    if matter_id is not None:
        statement = statement.where(Entity.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(Entity.matter_id.in_(matter_ids))
    return list(db.scalars(statement))


def _load_relationships(
    db: Session,
    matter_id: int | None,
    matter_ids: list[int] | None,
    document_ids: set[int],
) -> list[Relationship]:
    statement = select(Relationship)
    if matter_id is not None:
        statement = statement.where(Relationship.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(Relationship.matter_id.in_(matter_ids))
    if document_ids:
        statement = statement.where(Relationship.document_id.in_(document_ids))
    else:
        statement = statement.where(Relationship.document_id.is_(None))
    return list(db.scalars(statement))


def _load_custodians(db: Session) -> dict[int, Custodian]:
    return {custodian.id: custodian for custodian in db.scalars(select(Custodian))}


def _count_values(values) -> Counter[str]:
    return Counter(value or "Unknown" for value in values)


def _custodian_counts(documents: list[Document], custodians: dict[int, Custodian]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for document in documents:
        if document.custodian_id is None:
            counts["Unassigned"] += 1
            continue
        custodian = custodians.get(document.custodian_id)
        counts[custodian.full_name if custodian else "Unknown"] += 1
    return counts


def _document_timeline(documents: list[Document]) -> list[TimelinePoint]:
    counts: Counter[str] = Counter()
    for document in documents:
        timestamp = document.document_date or document.created_at
        counts[_date_label(timestamp)] += 1
    return [TimelinePoint(date=date, document_count=count) for date, count in sorted(counts.items())]


def _communication_pairs(db: Session, relationships: list[Relationship]) -> list[CommunicationMetric]:
    grouped: dict[tuple[int, int], list[Relationship]] = defaultdict(list)
    for relationship in relationships:
        if relationship.relationship_type == "communicated_with":
            grouped[(relationship.source_entity_id, relationship.target_entity_id)].append(relationship)

    metrics = []
    for (source_id, target_id), group in grouped.items():
        source = db.get(Entity, source_id)
        target = db.get(Entity, target_id)
        if source is None or target is None:
            continue
        metrics.append(
            CommunicationMetric(
                source_entity_id=source_id,
                source_entity_name=source.name,
                target_entity_id=target_id,
                target_entity_name=target.name,
                message_count=len(group),
                document_ids=sorted({relationship.document_id for relationship in group if relationship.document_id}),
            )
        )
    return sorted(metrics, key=lambda metric: (metric.message_count, metric.source_entity_name), reverse=True)[:20]


def _buckets(counts: Counter[str], limit: int | None = None) -> list[AnalyticsBucket]:
    items = counts.most_common(limit)
    return [AnalyticsBucket(label=label, count=count) for label, count in items]


def _date_label(value: datetime) -> str:
    return value.date().isoformat()
