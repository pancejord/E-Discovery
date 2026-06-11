# Phase 3 Changes

Date: 2026-06-11

## Purpose

Phase 3 adds entity extraction, entity persistence, cited mentions, and first-pass relationship extraction. This moves the platform from document-level RAG search toward a structured investigation workspace where people, organizations, dates, money values, legal references, locations, and email addresses can be reviewed across documents.

## Phase 2 Readiness Check

Phase 2 was verified before Phase 3 work began:

- Document chunking exists and stores chunk text, offsets, hashes, vector ids, and embeddings.
- Upload ingestion creates chunks for parsed text.
- Local deterministic embeddings support repeatable development and tests.
- Qdrant indexing is available behind `QDRANT_ENABLED=true`.
- `/api/search` returns chunk-level snippets, scores, and citations.
- Alembic migration `0002_document_chunks` applies cleanly.

Verification before Phase 3:

- `python -m pytest -q`: 4 tests passed.
- `python -m compileall -q app`: passed.
- `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///./tmp_phase2_audit.db`: passed.

No Phase 2 corrective edits were required before Phase 3. During Phase 3 integration, document cleanup relationships were added so entity mentions and document-scoped relationships are removed safely when a document is deleted.

## Phase 3 Implementation

The following capabilities were added:

- Rule-based named entity extraction for people, organizations, dates, money values, legal references, locations, and email addresses.
- Entity persistence through an `entities` table.
- Entity mention persistence through an `entity_mentions` table with document, chunk, offsets, and citation.
- Relationship persistence through a `relationships` table.
- Co-mention relationship extraction for entities appearing in the same chunk.
- Email header relationship extraction for sender-to-recipient communication.
- Entity API endpoints for listing entities, fetching cited mentions, and reviewing relationships.
- Tests covering entity extraction, cited mentions, co-mention relationships, and email communication relationships.

## Files Changed

- `backend/app/models/entity.py`
  Change: Added the `Entity` model.
  Purpose: Persist normalized named entities by matter and type.

- `backend/app/models/entity_mention.py`
  Change: Added the `EntityMention` model.
  Purpose: Preserve where each entity was found, including document, chunk, offsets, and citation.

- `backend/app/models/relationship.py`
  Change: Added the `Relationship` model.
  Purpose: Store evidence-backed relationships between entities.

- `backend/app/models/document.py`
  Change: Added cascading relationships for entity mentions and document-scoped relationships.
  Purpose: Keep derived entity data aligned with document deletion.

- `backend/app/models/__init__.py`
  Change: Exported Phase 3 models.
  Purpose: Keep model imports consistent for startup, migrations, and tests.

- `backend/app/database.py`
  Change: Imported Phase 3 models during local table initialization.
  Purpose: Ensure lightweight local startup creates entity and relationship tables.

- `backend/app/models/schemas.py`
  Change: Expanded entity schemas and added mention and relationship response schemas.
  Purpose: Return entity summaries, cited mentions, and relationship details through the API.

- `backend/app/services/entity_extraction.py`
  Change: Added rule-based extraction, entity upsert, mention creation, and relationship creation.
  Purpose: Implement Phase 3 entity and relationship extraction without requiring an external NLP model.

- `backend/app/services/ingestion.py`
  Change: Called entity processing after chunk creation and optional vector indexing.
  Purpose: Make uploaded documents immediately available for entity review.

- `backend/app/api/entities.py`
  Change: Replaced the placeholder entity endpoint with list, detail, and relationship endpoints.
  Purpose: Expose persisted Phase 3 data through the backend API.

- `backend/alembic/versions/0003_entities_relationships.py`
  Change: Added migration for entities, entity mentions, and relationships.
  Purpose: Version the Phase 3 database schema.

- `backend/tests/test_documents.py`
  Change: Added assertions for entity extraction, cited mentions, co-mention relationships, and email communication relationships.
  Purpose: Verify Phase 3 behavior through the existing upload workflow.

- `backend/README.md`
  Change: Documented the entity API and rule-based extraction behavior.
  Purpose: Help developers exercise Phase 3 locally.

- `docs/DATA_MODEL.md`
  Change: Added entity mention fields and expanded entity and relationship fields.
  Purpose: Keep the planning data model aligned with the implementation.

- `docs/CHANGE_LOG.md`
  Change: Added this Phase 3 project entry.
  Purpose: Maintain the project history in the existing change log.

- `docs/PHASE_3_CHANGES.md`
  Change: Added Phase 2 audit, Phase 3 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide the requested markdown record of changes and their purpose.

## Verification

- Run backend pytest.
- Run Python compile checks.
- Run Alembic upgrade against a temporary SQLite database.

Results:

- `python -m pytest -q`: 4 tests passed.
- `python -m compileall -q app`: passed.
- `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///./tmp_phase3_migration.db`: passed.

## Follow-Up Notes

- The current extractor is deterministic and rule-based. Later iterations can replace or augment it with spaCy or transformer NER.
- Relationship extraction currently covers co-mentions and email communication headers. Phase 4 can use these relationships as the seed for graph construction.
- Entity deduplication is normalized by lowercased name, matter, and type. More advanced alias resolution can be added after more sample data exists.
