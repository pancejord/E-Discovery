# Project Change Log

This file records meaningful project changes in plain language: what changed, which files were touched, and why the change was made.

## Process

Add a new entry whenever a backend, frontend, data, or infrastructure change is completed.

Each entry should include:

- Date
- Area of the project
- Goal
- Files changed
- Verification performed
- Follow-up notes, if any

For each file, use this format:

```text
- path/to/file
  Change: Short summary of what changed.
  Purpose: Why the change was needed.
```

## 2026-06-11 - Phase 5 Analytics Dashboard

Area: Backend and Frontend

Goal: Replace analytics placeholders with real dashboard data, Plotly charts, timeline analytics, and communication analysis.

### Files Changed

- `backend/app/models/schemas.py`
  Change: Added analytics bucket, timeline point, communication metric, and dashboard response schemas.
  Purpose: Provide typed contracts for Phase 5 analytics data.

- `backend/app/services/analytics.py`
  Change: Added analytics aggregation service.
  Purpose: Compute dashboard metrics from persisted documents, entities, custodians, and relationships.

- `backend/app/api/analytics.py`
  Change: Replaced placeholder snapshot values and added `/api/analytics/dashboard`.
  Purpose: Expose real analytics data to the frontend.

- `backend/tests/test_analytics.py`
  Change: Added tests for analytics snapshot and dashboard responses.
  Purpose: Verify counts, distributions, timelines, custodians, and communication pairs.

- `frontend/lib/api.ts`
  Change: Added analytics types and `getAnalyticsDashboard`.
  Purpose: Give the frontend typed access to dashboard data.

- `frontend/types/react-plotly.js.d.ts`
  Change: Added a minimal module declaration for `react-plotly.js`.
  Purpose: Allow TypeScript to compile Plotly dashboard components.

- `frontend/components/AnalyticsDashboardView.tsx`
  Change: Added the Plotly analytics dashboard UI.
  Purpose: Visualize document timelines, distributions, custodians, and communication pairs.

- `frontend/app/dashboard/page.tsx`
  Change: Replaced the placeholder dashboard with the analytics dashboard component.
  Purpose: Make `/dashboard` a working Phase 5 surface.

- `frontend/app/page.tsx`
  Change: Added a dashboard link to the workspace header.
  Purpose: Make analytics discoverable from the first screen.

- `backend/README.md`
  Change: Documented analytics API endpoints.
  Purpose: Help developers exercise the Phase 5 backend.

- `frontend/README.md`
  Change: Documented the dashboard page.
  Purpose: Help developers find the Phase 5 frontend view.

- `docs/PHASE_5_CHANGES.md`
  Change: Added Phase 4 audit, Phase 5 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide a dedicated record of the Phase 5 work.

### Verification

- Ran `python -m pytest -q`: 8 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.
- Ran `npm run build`.
- Ran a browser smoke test against `/dashboard` with temporary sample data: dashboard rendered metrics, Plotly chart content, and communication rows.

### Follow-Up Notes

- Analytics are dynamically computed from relational tables. Cached aggregate tables can be added later if dashboard latency becomes an issue.
- Phase 6 can use these metrics as part of regression fixtures.

## 2026-06-11 - Phase 4 Knowledge Graph Foundation

Area: Backend and Frontend

Goal: Add graph construction, graph queries, and relationship visualization on top of Phase 3 entity and relationship data.

### Files Changed

- `backend/app/models/schemas.py`
  Change: Added graph node, edge, metrics, graph response, and path response schemas.
  Purpose: Provide typed API contracts for graph visualization and graph queries.

- `backend/app/services/knowledge_graph.py`
  Change: Added NetworkX-backed graph construction, edge aggregation, metrics, neighborhood queries, and shortest-path queries.
  Purpose: Build knowledge graphs from persisted entities and relationships.

- `backend/app/api/graph.py`
  Change: Added graph, neighborhood, path, and metrics endpoints.
  Purpose: Expose Phase 4 graph capabilities through FastAPI.

- `backend/app/main.py`
  Change: Registered the graph router and added local-development CORS middleware.
  Purpose: Make graph APIs available to the browser frontend.

- `backend/tests/test_graph.py`
  Change: Added graph endpoint tests.
  Purpose: Verify visualization data, metrics, neighborhoods, shortest paths, and validation.

- `frontend/lib/api.ts`
  Change: Added graph types and `getKnowledgeGraph`.
  Purpose: Give the frontend typed access to `/api/graph`.

- `frontend/components/KnowledgeGraphView.tsx`
  Change: Added SVG graph visualization with metrics, selection, top entities, refresh, and relationship filtering.
  Purpose: Deliver the Phase 4 relationship visualization experience.

- `frontend/app/graph/page.tsx`
  Change: Added the `/graph` route.
  Purpose: Make the knowledge graph view available in the Next.js app.

- `frontend/app/page.tsx`
  Change: Added a graph link from the workspace header.
  Purpose: Make Phase 4 discoverable from the first screen.

- `backend/README.md`
  Change: Documented graph API endpoints.
  Purpose: Help developers exercise the Phase 4 backend.

- `frontend/README.md`
  Change: Documented the graph page.
  Purpose: Help developers find the Phase 4 frontend view.

- `docs/PHASE_4_CHANGES.md`
  Change: Added the Phase 4 audit, implementation summary, file list, verification, and follow-up notes.
  Purpose: Provide a dedicated record of the Phase 4 work.

### Verification

- Ran `python -m pytest -q`: 6 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.
- Ran `npm run build`.
- Ran a browser smoke test against `/graph` with temporary sample data: graph rendered with nodes, edges, metrics, selected entity details, and top entities.

### Follow-Up Notes

- The graph is built dynamically from relational data. A cached graph projection can be added later if graph size or latency requires it.
- Phase 5 can reuse graph metrics for dashboard widgets.

## 2026-06-11 - Backend Phase 3 Entity Extraction Foundation

Area: Backend

Goal: Verify Phase 2 and add persistent entity extraction, cited mentions, and first-pass relationship extraction.

### Files Changed

- `backend/app/models/entity.py`
  Change: Added the `Entity` model.
  Purpose: Persist normalized named entities by matter and type.

- `backend/app/models/entity_mention.py`
  Change: Added the `EntityMention` model.
  Purpose: Store cited entity mentions with document, chunk, and offset context.

- `backend/app/models/relationship.py`
  Change: Added the `Relationship` model.
  Purpose: Persist evidence-backed links between entities.

- `backend/app/models/document.py`
  Change: Added cascading relationships for entity mentions and document-scoped relationships.
  Purpose: Keep derived Phase 3 data aligned with document deletion.

- `backend/app/models/__init__.py`
  Change: Exported Phase 3 models.
  Purpose: Keep model imports consistent for startup, migrations, and tests.

- `backend/app/database.py`
  Change: Included Phase 3 models during local database initialization.
  Purpose: Ensure lightweight local development creates the new tables.

- `backend/app/models/schemas.py`
  Change: Added entity detail, mention, and relationship response schemas.
  Purpose: Return structured Phase 3 data from the API.

- `backend/app/services/entity_extraction.py`
  Change: Added rule-based NER, entity upsert, mention persistence, and relationship extraction.
  Purpose: Implement Phase 3 without requiring an external NLP service.

- `backend/app/services/ingestion.py`
  Change: Triggered entity processing after chunk creation.
  Purpose: Make uploaded documents immediately available for entity review.

- `backend/app/api/entities.py`
  Change: Replaced the placeholder route with entity list, detail, and relationship endpoints.
  Purpose: Expose persisted entities and relationships through `/api/entities`.

- `backend/alembic/versions/0003_entities_relationships.py`
  Change: Added migration for entities, entity mentions, and relationships.
  Purpose: Version the Phase 3 schema.

- `backend/tests/test_documents.py`
  Change: Added assertions for entity extraction, citations, and relationships.
  Purpose: Verify Phase 3 behavior through upload ingestion.

- `backend/README.md`
  Change: Documented entity API endpoints and extraction behavior.
  Purpose: Help developers exercise Phase 3 locally.

- `docs/DATA_MODEL.md`
  Change: Added entity mention fields and expanded entity and relationship fields.
  Purpose: Keep project docs aligned with the implementation.

- `docs/PHASE_3_CHANGES.md`
  Change: Added the Phase 2 audit, Phase 3 implementation summary, changed files, verification plan, and follow-up notes.
  Purpose: Provide the requested markdown record of Phase 3 changes.

### Verification

- Ran `python -m pytest -q`: 4 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.

### Follow-Up Notes

- The initial extractor is deterministic and rule-based. Future work can add spaCy, transformer NER, or provider-backed extraction.
- Relationship extraction currently covers co-mentions and email header communication.

## 2026-06-10 - Backend Phase 2 RAG Search Foundation

Area: Backend

Goal: Complete the Phase 1 parsing gaps and begin Phase 2 with chunked, citation-bearing search.

### Files Changed

- `backend/app/core/config.py`
  Change: Added Qdrant collection, Qdrant enablement, and embedding dimension settings.
  Purpose: Configure vector indexing while keeping local tests independent from external services.

- `backend/app/models/chunk.py`
  Change: Added the `DocumentChunk` model.
  Purpose: Persist searchable text chunks with offsets, hashes, embeddings, and vector ids.

- `backend/app/models/document.py`
  Change: Added a document-to-chunks relationship.
  Purpose: Tie chunk lifecycle to source document lifecycle.

- `backend/app/models/__init__.py`
  Change: Exported `DocumentChunk`.
  Purpose: Keep model imports consistent across startup, migrations, and tests.

- `backend/app/database.py`
  Change: Included chunk model loading in local database initialization.
  Purpose: Ensure the new table is created during lightweight local development.

- `backend/app/models/schemas.py`
  Change: Added chunk schema and expanded search result fields.
  Purpose: Return chunk ids, document ids, snippets, scores, and citations from search.

- `backend/app/services/text_extraction.py`
  Change: Added extraction for text, PDF, DOCX, and EML files.
  Purpose: Close the Phase 1 parsing gap required before useful RAG search.

- `backend/app/services/chunking.py`
  Change: Added overlapping text chunk generation.
  Purpose: Create citation-sized retrieval units from extracted document text.

- `backend/app/services/embeddings.py`
  Change: Added deterministic local embeddings and cosine similarity.
  Purpose: Enable repeatable vector-style retrieval without API keys.

- `backend/app/services/vector_store.py`
  Change: Added optional Qdrant collection setup and point indexing.
  Purpose: Prepare document chunks for Qdrant-backed retrieval when enabled.

- `backend/app/services/ingestion.py`
  Change: Wired extraction, metadata mapping, chunking, embeddings, and optional Qdrant indexing into upload ingestion.
  Purpose: Make uploaded documents immediately searchable.

- `backend/app/services/search.py`
  Change: Added database-backed chunk retrieval and ranking.
  Purpose: Replace placeholder search behavior with citation-bearing results.

- `backend/app/api/search.py`
  Change: Replaced stubbed search response with the retrieval service.
  Purpose: Expose the Phase 2 RAG foundation through `/api/search`.

- `backend/alembic/versions/0002_document_chunks.py`
  Change: Added migration for `document_chunks`.
  Purpose: Version the Phase 2 schema change.

- `backend/tests/test_documents.py`
  Change: Added assertions for parsing, metadata, and citation search.
  Purpose: Verify Phase 1 readiness and Phase 2 retrieval behavior.

- `.env.example`
  Change: Added Qdrant and embedding settings.
  Purpose: Document root environment configuration for Phase 2.

- `backend/.env.example`
  Change: Added Qdrant and embedding settings.
  Purpose: Document backend environment configuration for Phase 2.

- `backend/README.md`
  Change: Documented parsing and search behavior.
  Purpose: Help developers exercise the new workflow locally.

- `docs/DATA_MODEL.md`
  Change: Expanded the chunk model fields.
  Purpose: Keep the planning docs aligned with the implemented schema.

- `docs/PHASE_2_CHANGES.md`
  Change: Added Phase 1 audit, Phase 2 implementation summary, changed files, verification plan, and follow-up notes.
  Purpose: Provide the requested markdown record of changes and their purpose.

### Verification

- Ran `python -m pytest -q`: 4 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.

### Follow-Up Notes

- Direct Qdrant querying can be added after the vector service is part of the expected local runtime.
- The deterministic embedding provider should be replaced or made configurable when production model-provider decisions are finalized.

## 2026-06-09 - Backend Phase 1 Foundation

Area: Backend

Goal: Build the initial production-style backend foundation for document upload and persistence.

### Files Changed

- `backend/app/core/config.py`
  Change: Added `UPLOAD_DIR` configuration.
  Purpose: Allow uploaded document storage location to be controlled by environment settings.

- `backend/app/database.py`
  Change: Added SQLAlchemy engine, session factory, declarative base, database initializer, and `get_db` dependency.
  Purpose: Provide a reusable database layer for FastAPI routes and services.

- `backend/app/main.py`
  Change: Added startup database initialization and exposed document routes at both `/documents` and `/api/documents`.
  Purpose: Create tables during local development and support both the project plan API shape and the existing `/api` convention.

- `backend/app/models/matter.py`
  Change: Added `Matter` SQLAlchemy model.
  Purpose: Represent legal matters or cases that documents can belong to.

- `backend/app/models/custodian.py`
  Change: Added `Custodian` SQLAlchemy model.
  Purpose: Represent people or organizations whose documents are collected during eDiscovery.

- `backend/app/models/document.py`
  Change: Added `Document` SQLAlchemy model with upload, metadata, processing, and risk fields.
  Purpose: Persist uploaded legal document records and prepare the schema for later text extraction and analytics.

- `backend/app/models/__init__.py`
  Change: Exported `Matter`, `Custodian`, and `Document`.
  Purpose: Make model imports consistent for app startup, migrations, and tests.

- `backend/app/models/schemas.py`
  Change: Reworked document Pydantic schemas and added read schemas for matters and custodians.
  Purpose: Return structured API responses from persisted database records.

- `backend/app/api/documents.py`
  Change: Implemented document upload, list, detail, and delete endpoints.
  Purpose: Replace placeholder in-memory upload inspection with real document persistence and file storage.

- `backend/app/services/ingestion.py`
  Change: Added upload ingestion service and document lookup helper.
  Purpose: Keep API routes thin while centralizing document creation logic.

- `backend/app/utils/file_utils.py`
  Change: Added filename sanitization, file extension detection, and streamed upload saving.
  Purpose: Store uploaded files safely and avoid loading large files entirely into memory.

- `backend/app/utils/time.py`
  Change: Added timezone-aware UTC timestamp helper.
  Purpose: Avoid deprecated `datetime.utcnow()` usage and keep timestamps consistent.

- `backend/app/utils/__init__.py`
  Change: Added utils package marker.
  Purpose: Support imports from backend utility modules.

- `backend/tests/test_documents.py`
  Change: Added tests for upload, list, detail, delete, matter/custodian linkage, and invalid matter validation.
  Purpose: Verify the Phase 1 document workflow against an isolated SQLite database and temporary upload directory.

- `backend/requirements.txt`
  Change: Added Alembic.
  Purpose: Support database migrations for production-style schema management.

- `backend/alembic.ini`
  Change: Added Alembic configuration.
  Purpose: Configure migration discovery and database URL handling.

- `backend/alembic/env.py`
  Change: Added migration environment wired to app settings and SQLAlchemy metadata.
  Purpose: Let Alembic generate and run migrations from the app models.

- `backend/alembic/script.py.mako`
  Change: Added Alembic migration template.
  Purpose: Standardize future migration file generation.

- `backend/alembic/versions/0001_initial_foundation.py`
  Change: Added initial migration for matters, custodians, and documents.
  Purpose: Create the Phase 1 database schema through Alembic.

- `backend/.env.example`
  Change: Added `UPLOAD_DIR`.
  Purpose: Document the environment setting for uploaded file storage.

- `backend/README.md`
  Change: Added migration command, document API notes, and database/storage guidance.
  Purpose: Make local setup and the new backend endpoints easier to run and understand.

### Verification

- Ran `python -m pytest -q`: 4 tests passed.
- Ran `python -m pip check`: no broken requirements found.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.
- Ran `python -m compileall -q app`.

### Follow-Up Notes

- Next backend phase should add document text extraction and metadata extraction for PDF, DOCX, and EML files.
- Docker was not available on PATH during setup, so PostgreSQL and Qdrant services were not started locally.
