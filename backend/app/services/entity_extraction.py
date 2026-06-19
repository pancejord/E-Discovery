import re
from dataclasses import dataclass
from email.utils import getaddresses
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.models.entity import Entity
from app.models.entity_mention import EntityMention
from app.models.relationship import Relationship

EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
MONEY_PATTERN = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?|\b\d[\d,]*(?:\.\d{2})?\s?(?:USD|dollars)\b", re.IGNORECASE)
DATE_PATTERN = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{1,2},?\s+\d{4}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    re.IGNORECASE,
)
LEGAL_REFERENCE_PATTERN = re.compile(
    r"\b(?:Fed\.\s*R\.\s*Civ\.\s*P\.|Rule|Section|Sec\.)\s*\d+(?:\.\d+)?\b",
    re.IGNORECASE,
)
ORG_PATTERN = re.compile(
    r"\b(?:[A-Z][A-Za-z&.'-]+(?:\s+|$)){1,5}"
    r"(?:LLC|L\.L\.C\.|Inc\.?|Corp\.?|Corporation|Company|Co\.|Ltd\.?|LLP|Bank|Group|Partners)\b"
)
PERSON_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b")
LOCATION_PATTERN = re.compile(
    r"\b(?:New York|California|Delaware|Texas|Florida|Washington|Chicago|Los Angeles|San Francisco|Boston)\b"
)

ORG_SUFFIXES = {"llc", "l.l.c.", "inc", "inc.", "corp", "corp.", "corporation", "company", "co.", "ltd", "ltd.", "llp"}
ORG_SUFFIX_NORMALIZATIONS = {
    "corporation": "corp",
    "corp.": "corp",
    "inc.": "inc",
    "company": "co",
    "co.": "co",
    "ltd.": "ltd",
    "l.l.c.": "llc",
}
PERSON_EXCLUSIONS = {
    "United States",
    "New York",
    "San Francisco",
    "Los Angeles",
    "January",
    "February",
    "March",
    "April",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
}


@dataclass(frozen=True)
class ExtractedMention:
    name: str
    entity_type: str
    char_start: int
    char_end: int
    citation: str


def process_document_entities(db: Session, document: Document, chunks: list[DocumentChunk]) -> None:
    mentions_by_entity: dict[tuple[int | None, str, str], Entity] = {}
    chunk_entity_ids: dict[int, list[int]] = {}

    for chunk in chunks:
        chunk_entities: list[Entity] = []
        for mention in extract_chunk_mentions(document, chunk):
            entity = _get_or_create_entity(db, document.matter_id, mention.name, mention.entity_type)
            mentions_by_entity[(entity.matter_id, entity.entity_type, entity.normalized_name)] = entity
            db.add(
                EntityMention(
                    entity=entity,
                    document_id=document.id,
                    chunk_id=chunk.id,
                    mention_text=mention.name,
                    char_start=mention.char_start,
                    char_end=mention.char_end,
                    citation=mention.citation,
                )
            )
            chunk_entities.append(entity)
        chunk_entity_ids[chunk.id] = _unique_entity_ids(chunk_entities)

    db.flush()
    _add_header_relationships(db, document)
    _add_chunk_relationships(db, document, chunks, chunk_entity_ids)
    db.commit()


def extract_chunk_mentions(document: Document, chunk: DocumentChunk) -> list[ExtractedMention]:
    candidates: list[tuple[str, str, int, int]] = []
    for entity_type, pattern in (
        ("EMAIL_ADDRESS", EMAIL_PATTERN),
        ("MONEY", MONEY_PATTERN),
        ("DATE", DATE_PATTERN),
        ("LEGAL_REFERENCE", LEGAL_REFERENCE_PATTERN),
        ("ORGANIZATION", ORG_PATTERN),
        ("PERSON", PERSON_PATTERN),
        ("LOCATION", LOCATION_PATTERN),
    ):
        for match in pattern.finditer(chunk.text):
            value = match.group(0).strip()
            if _should_keep(value, entity_type):
                candidates.append((value, entity_type, match.start(), match.end()))

    seen: set[tuple[str, str, int]] = set()
    mentions = []
    for value, entity_type, start, end in sorted(candidates, key=lambda item: (item[2], item[3])):
        key = (normalize_entity_name(value, entity_type), entity_type, start)
        if key in seen:
            continue
        seen.add(key)
        global_start = chunk.char_start + start
        global_end = chunk.char_start + end
        mentions.append(
            ExtractedMention(
                name=value,
                entity_type=entity_type,
                char_start=global_start,
                char_end=global_end,
                citation=f"{document.original_filename}#chunk-{chunk.chunk_index + 1}:{global_start}-{global_end}",
            )
        )
    return mentions


def normalize_entity_name(name: str, entity_type: str | None = None) -> str:
    normalized = re.sub(r"\s+", " ", name.strip().lower()).strip(".,;:()[]{}\"'")
    if entity_type == "ORGANIZATION":
        parts = normalized.split()
        if parts:
            suffix = parts[-1]
            parts[-1] = ORG_SUFFIX_NORMALIZATIONS.get(suffix, suffix)
        return " ".join(parts)
    if entity_type == "PERSON":
        return re.sub(r"\s+[<\(].*$", "", normalized).strip()
    return normalized


def _get_or_create_entity(db: Session, matter_id: int | None, name: str, entity_type: str) -> Entity:
    normalized_name = normalize_entity_name(name, entity_type)
    statement = select(Entity).where(
        Entity.matter_id.is_(None) if matter_id is None else Entity.matter_id == matter_id,
        Entity.entity_type == entity_type,
        Entity.normalized_name == normalized_name,
    )
    entity = db.scalar(statement)
    if entity is not None:
        return entity

    entity = Entity(
        matter_id=matter_id,
        name=name,
        entity_type=entity_type,
        normalized_name=normalized_name,
    )
    db.add(entity)
    db.flush()
    return entity


def _add_header_relationships(db: Session, document: Document) -> None:
    sender_entities = _entities_from_header(db, document.matter_id, document.sender)
    recipient_entities = _entities_from_header(db, document.matter_id, document.recipients)
    for sender in sender_entities:
        for recipient in recipient_entities:
            if sender.id != recipient.id:
                _get_or_create_relationship(
                    db,
                    document,
                    sender.id,
                    "communicated_with",
                    recipient.id,
                    0.95,
                    f"Email header in {document.original_filename}",
                )


def _add_chunk_relationships(
    db: Session,
    document: Document,
    chunks: list[DocumentChunk],
    chunk_entity_ids: dict[int, list[int]],
) -> None:
    citation_by_chunk_id = {
        chunk.id: f"{document.original_filename}#chunk-{chunk.chunk_index + 1}:{chunk.char_start}-{chunk.char_end}"
        for chunk in chunks
    }
    for chunk_id, entity_ids in chunk_entity_ids.items():
        for source_id, target_id in combinations(entity_ids[:8], 2):
            _get_or_create_relationship(
                db,
                document,
                source_id,
                "mentioned_with",
                target_id,
                0.55,
                citation_by_chunk_id.get(chunk_id),
            )


def _entities_from_header(db: Session, matter_id: int | None, header_value: str | None) -> list[Entity]:
    entities = []
    for display_name, address in getaddresses([header_value or ""]):
        if display_name:
            entities.append(_get_or_create_entity(db, matter_id, display_name, "PERSON"))
        if address:
            entities.append(_get_or_create_entity(db, matter_id, address, "EMAIL_ADDRESS"))
    return entities


def _get_or_create_relationship(
    db: Session,
    document: Document,
    source_entity_id: int,
    relationship_type: str,
    target_entity_id: int,
    confidence: float,
    evidence: str | None,
) -> Relationship:
    statement = select(Relationship).where(
        Relationship.matter_id.is_(None) if document.matter_id is None else Relationship.matter_id == document.matter_id,
        Relationship.source_entity_id == source_entity_id,
        Relationship.relationship_type == relationship_type,
        Relationship.target_entity_id == target_entity_id,
        Relationship.document_id == document.id,
    )
    relationship = db.scalar(statement)
    if relationship is not None:
        return relationship

    relationship = Relationship(
        matter_id=document.matter_id,
        source_entity_id=source_entity_id,
        relationship_type=relationship_type,
        target_entity_id=target_entity_id,
        document_id=document.id,
        confidence=confidence,
        evidence=evidence,
    )
    db.add(relationship)
    return relationship


def _unique_entity_ids(entities: list[Entity]) -> list[int]:
    seen = set()
    unique_ids = []
    for entity in entities:
        if entity.id in seen:
            continue
        seen.add(entity.id)
        unique_ids.append(entity.id)
    return unique_ids


def _should_keep(value: str, entity_type: str) -> bool:
    normalized = normalize_entity_name(value, entity_type)
    if entity_type == "PERSON":
        if any(exclusion.lower() == normalized for exclusion in PERSON_EXCLUSIONS):
            return False
        if any(normalized.endswith(suffix) for suffix in ORG_SUFFIXES):
            return False
    return True
