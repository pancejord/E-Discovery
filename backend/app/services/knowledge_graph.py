from collections import defaultdict

import networkx as nx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entity import Entity
from app.models.entity_mention import EntityMention
from app.models.relationship import Relationship
from app.models.schemas import GraphEdge, GraphMetrics, GraphNode, KnowledgeGraphResponse


def build_knowledge_graph(
    db: Session,
    matter_id: int | None = None,
    matter_ids: list[int] | None = None,
    relationship_type: str | None = None,
    min_confidence: float = 0.0,
    entity_limit: int = 250,
) -> KnowledgeGraphResponse:
    entities = _load_entities(db, matter_id, entity_limit, matter_ids=matter_ids)
    relationships = _load_relationships(
        db,
        entity_ids=set(entities),
        matter_id=matter_id,
        matter_ids=matter_ids,
        relationship_type=relationship_type,
        min_confidence=min_confidence,
    )
    return _response_from_graph(entities, relationships, _load_mention_counts(db, set(entities)))


def build_neighborhood(
    db: Session,
    entity_id: int,
    depth: int = 1,
    relationship_type: str | None = None,
    min_confidence: float = 0.0,
) -> KnowledgeGraphResponse:
    root = db.get(Entity, entity_id)
    if root is None:
        raise ValueError("Entity not found")

    all_entities = _load_entities(db, root.matter_id, 1000, scope_to_matter=True)
    all_relationships = _load_relationships(
        db,
        entity_ids=set(all_entities),
        matter_id=root.matter_id,
        scope_to_matter=True,
        relationship_type=relationship_type,
        min_confidence=min_confidence,
    )
    graph = _networkx_graph(all_entities, all_relationships)
    if entity_id not in graph:
        return _response_from_graph({entity_id: all_entities[entity_id]}, [], _load_mention_counts(db, {entity_id}))

    neighborhood_ids = {
        node
        for node, distance in nx.single_source_shortest_path_length(graph.to_undirected(), entity_id, cutoff=depth).items()
        if distance <= depth
    }
    entities = {entity_id: entity for entity_id, entity in all_entities.items() if entity_id in neighborhood_ids}
    relationships = [
        relationship
        for relationship in all_relationships
        if relationship.source_entity_id in neighborhood_ids and relationship.target_entity_id in neighborhood_ids
    ]
    return _response_from_graph(entities, relationships, _load_mention_counts(db, neighborhood_ids))


def shortest_paths(
    db: Session,
    source_entity_id: int,
    target_entity_id: int,
    max_depth: int = 4,
) -> list[list[GraphNode]]:
    source = db.get(Entity, source_entity_id)
    target = db.get(Entity, target_entity_id)
    if source is None or target is None:
        raise ValueError("Entity not found")
    if source.matter_id != target.matter_id:
        return []

    entities = _load_entities(db, source.matter_id, 1000, scope_to_matter=True)
    relationships = _load_relationships(
        db,
        entity_ids=set(entities),
        matter_id=source.matter_id,
        scope_to_matter=True,
    )
    graph = _networkx_graph(entities, relationships).to_undirected()
    mention_counts = _load_mention_counts(db, set(entities))
    if source_entity_id not in graph or target_entity_id not in graph:
        return []

    paths = []
    try:
        for path in nx.all_shortest_paths(graph, source_entity_id, target_entity_id):
            if len(path) - 1 <= max_depth:
                paths.append(
                    [
                        _node_schema(entities[node_id], graph.degree[node_id], mention_counts.get(node_id, 0))
                        for node_id in path
                    ]
                )
            if len(paths) >= 5:
                break
    except nx.NetworkXNoPath:
        return []
    return paths


def _load_entities(
    db: Session,
    matter_id: int | None,
    limit: int,
    scope_to_matter: bool = False,
    matter_ids: list[int] | None = None,
) -> dict[int, Entity]:
    mention_counts = (
        select(EntityMention.entity_id, func.count(EntityMention.id).label("mention_count"))
        .group_by(EntityMention.entity_id)
        .subquery()
    )
    statement = select(Entity).outerjoin(mention_counts, mention_counts.c.entity_id == Entity.id)
    if matter_id is not None:
        statement = statement.where(Entity.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(Entity.matter_id.in_(matter_ids))
    elif scope_to_matter:
        statement = statement.where(Entity.matter_id.is_(None))
    statement = statement.order_by(func.coalesce(mention_counts.c.mention_count, 0).desc(), Entity.name).limit(limit)
    return {entity.id: entity for entity in db.scalars(statement)}


def _load_relationships(
    db: Session,
    entity_ids: set[int],
    matter_id: int | None,
    scope_to_matter: bool = False,
    matter_ids: list[int] | None = None,
    relationship_type: str | None = None,
    min_confidence: float = 0.0,
) -> list[Relationship]:
    if not entity_ids:
        return []
    statement = select(Relationship).where(
        Relationship.source_entity_id.in_(entity_ids),
        Relationship.target_entity_id.in_(entity_ids),
        Relationship.confidence >= min_confidence,
    )
    if matter_id is not None:
        statement = statement.where(Relationship.matter_id == matter_id)
    elif matter_ids is not None:
        statement = statement.where(Relationship.matter_id.in_(matter_ids))
    elif scope_to_matter:
        statement = statement.where(Relationship.matter_id.is_(None))
    if relationship_type is not None:
        statement = statement.where(Relationship.relationship_type == relationship_type)
    return list(db.scalars(statement.order_by(Relationship.confidence.desc(), Relationship.id)))


def _load_mention_counts(db: Session, entity_ids: set[int]) -> dict[int, int]:
    if not entity_ids:
        return {}
    statement = (
        select(EntityMention.entity_id, func.count(EntityMention.id))
        .where(EntityMention.entity_id.in_(entity_ids))
        .group_by(EntityMention.entity_id)
    )
    return {entity_id: mention_count for entity_id, mention_count in db.execute(statement).all()}


def _response_from_graph(
    entities: dict[int, Entity],
    relationships: list[Relationship],
    mention_counts: dict[int, int],
) -> KnowledgeGraphResponse:
    graph = _networkx_graph(entities, relationships)
    nodes = [
        _node_schema(entity, graph.degree[entity_id] if entity_id in graph else 0, mention_counts.get(entity_id, 0))
        for entity_id, entity in entities.items()
    ]
    edges = _edge_schemas(relationships)
    metrics = _graph_metrics(graph, nodes, edges)
    return KnowledgeGraphResponse(nodes=nodes, edges=edges, metrics=metrics)


def _networkx_graph(entities: dict[int, Entity], relationships: list[Relationship]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for entity_id, entity in entities.items():
        graph.add_node(entity_id, label=entity.name, entity_type=entity.entity_type)
    for relationship in relationships:
        graph.add_edge(
            relationship.source_entity_id,
            relationship.target_entity_id,
            key=f"{relationship.relationship_type}:{relationship.document_id}",
            relationship_type=relationship.relationship_type,
            confidence=relationship.confidence,
        )
    return graph


def _edge_schemas(relationships: list[Relationship]) -> list[GraphEdge]:
    grouped: dict[tuple[int, int, str], list[Relationship]] = defaultdict(list)
    for relationship in relationships:
        grouped[(relationship.source_entity_id, relationship.target_entity_id, relationship.relationship_type)].append(relationship)

    edges = []
    for (source_id, target_id, relationship_type), group in grouped.items():
        document_ids = sorted({relationship.document_id for relationship in group if relationship.document_id is not None})
        evidence = [relationship.evidence for relationship in group if relationship.evidence]
        average_confidence = sum(relationship.confidence for relationship in group) / len(group)
        edges.append(
            GraphEdge(
                id=f"{source_id}:{relationship_type}:{target_id}",
                source=source_id,
                target=target_id,
                relationship_type=relationship_type,
                weight=len(group),
                confidence=round(average_confidence, 4),
                document_ids=document_ids,
                evidence=evidence[:5],
            )
        )
    return sorted(edges, key=lambda edge: (edge.relationship_type, edge.source, edge.target))


def _graph_metrics(graph: nx.MultiDiGraph, nodes: list[GraphNode], edges: list[GraphEdge]) -> GraphMetrics:
    undirected = graph.to_undirected()
    connected_component_count = nx.number_connected_components(undirected) if undirected.number_of_nodes() else 0
    density = nx.density(undirected) if undirected.number_of_nodes() > 1 else 0.0
    top_entities = sorted(nodes, key=lambda node: (node.degree, node.mention_count, node.label), reverse=True)[:10]
    return GraphMetrics(
        node_count=len(nodes),
        edge_count=len(edges),
        connected_component_count=connected_component_count,
        density=round(density, 4),
        top_entities=top_entities,
    )


def _node_schema(entity: Entity, degree: int, mention_count: int) -> GraphNode:
    return GraphNode(
        id=entity.id,
        label=entity.name,
        entity_type=entity.entity_type,
        mention_count=mention_count,
        degree=degree,
    )
