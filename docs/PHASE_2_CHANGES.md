# Phase 2 Changes

Date: 2026-06-10

## Purpose

Phase 2 begins the RAG search foundation for the litigation and eDiscovery analytics platform. The goal is to make uploaded documents searchable through persisted chunks, deterministic embeddings, optional Qdrant indexing, and citation-bearing search responses.

## Phase 1 Readiness Check

Phase 1 had a strong persistence foundation already in place:

- Upload endpoints existed at `/documents/upload` and `/api/documents/upload`.
- Uploaded files were stored on disk.
- Document records were persisted through SQLAlchemy.
- Matter and custodian validation existed.
- List, detail, and delete document endpoints existed.
- Alembic migration support existed for the initial database schema.
- Backend tests covered upload, list, detail, delete, and validation flows.

Before starting Phase 2, the remaining Phase 1 gaps were closed:

- Upload ingestion now extracts text from supported files.
- EML headers are mapped into sender, recipients, subject, and document date fields.
- Simple rule-based document classification now populates `document_type`.
- Text hashes now populate for parsed documents.
- Processing status now reflects parsing success with `parsed`.

## Phase 2 Implementation

The following capabilities were added:

- Document chunking for extracted text.
- A `document_chunks` table and SQLAlchemy model.
- Deterministic local embeddings for chunks and search queries.
- Optional Qdrant collection creation and chunk upsert when `QDRANT_ENABLED=true`.
- Citation construction using filename, chunk number, and character offsets.
- A real `/api/search` implementation that ranks chunks and returns document-level citations.
- Tests that verify parsed upload content can be searched with citations.

## Files Changed

- `backend/app/core/config.py`
  Change: Added Qdrant collection, Qdrant enablement, and embedding dimension settings.
  Purpose: Configure Phase 2 vector search behavior without requiring external services for local tests.

- `backend/app/models/chunk.py`
  Change: Added the `DocumentChunk` SQLAlchemy model.
  Purpose: Persist chunk text, offsets, hashes, embeddings, vector ids, and embedding metadata.

- `backend/app/models/document.py`
  Change: Added a cascading relationship from documents to chunks.
  Purpose: Keep chunk lifecycle tied to the source document.

- `backend/app/models/__init__.py`
  Change: Exported `DocumentChunk`.
  Purpose: Keep model imports consistent for startup, migrations, and tests.

- `backend/app/database.py`
  Change: Imported the chunk model during local table initialization.
  Purpose: Ensure lightweight SQLite startup creates the new chunk table.

- `backend/app/models/schemas.py`
  Change: Added chunk read schema and expanded search result fields.
  Purpose: Return typed chunk ids, document ids, snippets, scores, and citations.

- `backend/app/services/text_extraction.py`
  Change: Added extraction support for text files, PDFs, DOCX files, and EML messages.
  Purpose: Complete the Phase 1 parsing foundation needed for RAG retrieval.

- `backend/app/services/chunking.py`
  Change: Added overlapping text chunk generation.
  Purpose: Break parsed documents into retrievable citation units.

- `backend/app/services/embeddings.py`
  Change: Added deterministic local hash embeddings and cosine similarity.
  Purpose: Support repeatable vector-style retrieval without requiring external API keys.

- `backend/app/services/vector_store.py`
  Change: Added optional Qdrant collection setup and point upsert.
  Purpose: Prepare the backend for Qdrant-backed vector retrieval.

- `backend/app/services/ingestion.py`
  Change: Wired parsing, metadata extraction, chunking, embeddings, and optional Qdrant indexing into upload ingestion.
  Purpose: Make newly uploaded documents immediately searchable.

- `backend/app/services/search.py`
  Change: Added chunk retrieval and ranking service.
  Purpose: Combine lexical and embedding scores into citation-bearing search results.

- `backend/app/api/search.py`
  Change: Replaced the placeholder response with database-backed chunk search.
  Purpose: Expose the Phase 2 RAG retrieval foundation through the API.

- `backend/alembic/versions/0002_document_chunks.py`
  Change: Added a migration for the `document_chunks` table and indexes.
  Purpose: Version the Phase 2 database schema.

- `backend/tests/test_documents.py`
  Change: Updated upload expectations and added citation search assertions.
  Purpose: Verify that Phase 1 parsing and Phase 2 search work together.

- `backend/.env.example`
  Change: Added Qdrant and embedding settings.
  Purpose: Document local configuration for Phase 2.

- `.env.example`
  Change: Added Qdrant and embedding settings.
  Purpose: Keep root environment documentation aligned with backend settings.

- `backend/README.md`
  Change: Documented parsing and search API behavior.
  Purpose: Help developers run and exercise the new workflow.

- `docs/DATA_MODEL.md`
  Change: Expanded the chunk model fields.
  Purpose: Keep planning docs aligned with the implemented schema.

- `docs/CHANGE_LOG.md`
  Change: Added the Phase 2 entry.
  Purpose: Maintain the project history in the existing change log.

## Verification

- Run backend pytest.
- Run Python compile checks.
- Run Alembic upgrade against a temporary SQLite database.

Results:

- `python -m pytest -q`: 4 tests passed.
- `python -m compileall -q app`: passed.
- `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///./tmp_phase2_migration.db`: passed.

## Follow-Up Notes

- Qdrant indexing is currently optional and best exercised with Docker running.
- The local embedding provider is deterministic and suitable for development; production can later switch to OpenAI, Azure OpenAI, or sentence-transformer embeddings.
- The search endpoint currently retrieves from persisted chunks. A later Phase 2 increment can add direct Qdrant querying once the vector service is part of the normal local runtime.
