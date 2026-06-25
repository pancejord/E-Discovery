import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.utils import getaddresses
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
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
    provider: str = "deterministic"


class EntityExtractionProvider(ABC):
    name: str

    @abstractmethod
    def extract(self, document: Document, chunk: DocumentChunk) -> list[ExtractedMention]:
        raise NotImplementedError


class DeterministicEntityProvider(EntityExtractionProvider):
    name = "deterministic"

    def extract(self, document: Document, chunk: DocumentChunk) -> list[ExtractedMention]:
        return _deterministic_mentions(document, chunk, self.name)


class SpacyEntityProvider(EntityExtractionProvider):
    name = "spacy"

    def __init__(self) -> None:
        self._nlp = None

    def extract(self, document: Document, chunk: DocumentChunk) -> list[ExtractedMention]:
        if self._nlp is None:
            try:
                import spacy

                self._nlp = spacy.load(settings.spacy_model)
            except Exception:
                return _deterministic_mentions(document, chunk, "deterministic_fallback")

        mentions = []
        doc = self._nlp(chunk.text)
        for ent in doc.ents:
            entity_type = _spacy_label(ent.label_)
            if entity_type is None:
                continue
            value = ent.text.strip()
            if not value or not _should_keep(value, entity_type):
                continue
            global_start = chunk.char_start + ent.start_char
            global_end = chunk.char_start + ent.end_char
            mentions.append(
                ExtractedMention(
                    name=value,
                    entity_type=entity_type,
                    char_start=global_start,
                    char_end=global_end,
                    citation=f"{document.original_filename}#chunk-{chunk.chunk_index + 1}:{global_start}-{global_end}",
                    provider=self.name,
                )
            )
        if not mentions:
            return _deterministic_mentions(document, chunk, "deterministic_fallback")
        return _dedupe_mentions(mentions)


def process_document_entities(db: Session, document: Document, chunks: list[DocumentChunk]) -> None:
    mentions_by_entity: dict[tuple[int | None, str, str], Entity] = {}
    chunk_entities_by_id: dict[int, list[Entity]] = {}
    provider = _provider()

    for chunk in chunks:
        chunk_entities: list[Entity] = []
        for mention in provider.extract(document, chunk):
            entity = _get_or_create_entity(
                db,
                document.matter_id,
                mention.name,
                mention.entity_type,
                provider=mention.provider,
            )
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
        chunk_entities_by_id[chunk.id] = _unique_entities(chunk_entities)

    db.flush()
    _add_header_relationships(db, document)
    _add_chunk_relationships(db, document, chunks, chunk_entities_by_id)
    db.commit()


def extract_chunk_mentions(document: Document, chunk: DocumentChunk) -> list[ExtractedMention]:
    return _provider().extract(document, chunk)


def _deterministic_mentions(document: Document, chunk: DocumentChunk, provider: str) -> list[ExtractedMention]:
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
                provider=provider,
            )
        )
    return _dedupe_mentions(mentions)


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


def _get_or_create_entity(
    db: Session,
    matter_id: int | None,
    name: str,
    entity_type: str,
    provider: str = "deterministic",
) -> Entity:
    normalized_name = normalize_entity_name(name, entity_type)
    statement = select(Entity).where(
        Entity.matter_id.is_(None) if matter_id is None else Entity.matter_id == matter_id,
        Entity.entity_type == entity_type,
        Entity.normalized_name == normalized_name,
    )
    entity = db.scalar(statement)
    if entity is not None:
        if not entity.extraction_provider:
            entity.extraction_provider = provider
        return entity

    entity = Entity(
        matter_id=matter_id,
        name=name,
        entity_type=entity_type,
        normalized_name=normalized_name,
        extraction_provider=provider,
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
                    "Email sender and recipient headers provide direct communication evidence.",
                )


def _add_chunk_relationships(
    db: Session,
    document: Document,
    chunks: list[DocumentChunk],
    chunk_entities_by_id: dict[int, list[Entity]],
) -> None:
    citation_by_chunk_id = {
        chunk.id: f"{document.original_filename}#chunk-{chunk.chunk_index + 1}:{chunk.char_start}-{chunk.char_end}"
        for chunk in chunks
    }
    for chunk_id, entities in chunk_entities_by_id.items():
        entities = chunk_entities_by_id.get(chunk_id, [])
        entity_ids = [entity.id for entity in entities]
        for source_id, target_id in combinations(entity_ids[:8], 2):
            _get_or_create_relationship(
                db,
                document,
                source_id,
                "mentioned_with",
                target_id,
                0.55,
                citation_by_chunk_id.get(chunk_id),
                "Entities appear in the same extracted text chunk.",
            )
        _add_typed_relationships(db, document, entities, citation_by_chunk_id.get(chunk_id))


def _add_typed_relationships(
    db: Session,
    document: Document,
    entities: list[Entity],
    evidence: str | None,
) -> None:
    people = [entity for entity in entities if entity.entity_type in {"PERSON", "EMAIL_ADDRESS"}]
    organizations = [entity for entity in entities if entity.entity_type == "ORGANIZATION"]
    money_values = [entity for entity in entities if entity.entity_type == "MONEY"]
    legal_refs = [entity for entity in entities if entity.entity_type == "LEGAL_REFERENCE"]
    locations = [entity for entity in entities if entity.entity_type == "LOCATION"]
    dates = [entity for entity in entities if entity.entity_type == "DATE"]

    for actor in people[:4]:
        for organization in organizations[:4]:
            _get_or_create_relationship(
                db,
                document,
                actor.id,
                "associated_with",
                organization.id,
                0.68,
                evidence,
                "Person or email address is mentioned near an organization in the same chunk.",
            )
    for organization in organizations[:4]:
        for money in money_values[:4]:
            _get_or_create_relationship(
                db,
                document,
                organization.id,
                "monetary_reference",
                money.id,
                0.72,
                evidence,
                "Organization is mentioned near a money value in the same chunk.",
            )
        for legal_ref in legal_refs[:4]:
            _get_or_create_relationship(
                db,
                document,
                organization.id,
                "legal_reference",
                legal_ref.id,
                0.7,
                evidence,
                "Organization is mentioned near a rule or section reference in the same chunk.",
            )
        for location in locations[:3]:
            _get_or_create_relationship(
                db,
                document,
                organization.id,
                "located_in",
                location.id,
                0.62,
                evidence,
                "Organization is mentioned near a location in the same chunk.",
            )
    for actor in [*people[:4], *organizations[:4]]:
        for date in dates[:4]:
            _get_or_create_relationship(
                db,
                document,
                actor.id,
                "dated_event",
                date.id,
                0.64,
                evidence,
                "Entity is mentioned near a date in the same chunk.",
            )


def _entities_from_header(db: Session, matter_id: int | None, header_value: str | None) -> list[Entity]:
    entities = []
    for display_name, address in getaddresses([header_value or ""]):
        if display_name:
            entities.append(_get_or_create_entity(db, matter_id, display_name, "PERSON", provider="email_header"))
        if address:
            entities.append(_get_or_create_entity(db, matter_id, address, "EMAIL_ADDRESS", provider="email_header"))
    return entities


def _get_or_create_relationship(
    db: Session,
    document: Document,
    source_entity_id: int,
    relationship_type: str,
    target_entity_id: int,
    confidence: float,
    evidence: str | None,
    confidence_explanation: str | None,
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
        confidence_explanation=confidence_explanation,
    )
    db.add(relationship)
    return relationship


def _unique_entities(entities: list[Entity]) -> list[Entity]:
    seen = set()
    unique_entities = []
    for entity in entities:
        if entity.id in seen:
            continue
        seen.add(entity.id)
        unique_entities.append(entity)
    return unique_entities


def _dedupe_mentions(mentions: list[ExtractedMention]) -> list[ExtractedMention]:
    seen: set[tuple[str, str, int]] = set()
    unique_mentions = []
    for mention in sorted(mentions, key=lambda item: (item.char_start, item.char_end, item.name)):
        key = (normalize_entity_name(mention.name, mention.entity_type), mention.entity_type, mention.char_start)
        if key in seen:
            continue
        seen.add(key)
        unique_mentions.append(mention)
    return unique_mentions


def _provider() -> EntityExtractionProvider:
    if settings.entity_extraction_provider.lower() == "spacy":
        return SpacyEntityProvider()
    return DeterministicEntityProvider()


def _spacy_label(label: str) -> str | None:
    return {
        "PERSON": "PERSON",
        "ORG": "ORGANIZATION",
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "DATE": "DATE",
        "MONEY": "MONEY",
        "LAW": "LEGAL_REFERENCE",
    }.get(label)


def _should_keep(value: str, entity_type: str) -> bool:
    normalized = normalize_entity_name(value, entity_type)
    if entity_type == "PERSON":
        if any(exclusion.lower() == normalized for exclusion in PERSON_EXCLUSIONS):
            return False
        if any(normalized.endswith(suffix) for suffix in ORG_SUFFIXES):
            return False
    return True
