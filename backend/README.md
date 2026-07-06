# Backend

FastAPI service for ingestion, metadata extraction, search, analytics, entity extraction, knowledge graph construction, and AI evaluation.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API docs will be available at `http://localhost:8000/docs`.

## Document API

The document router is available at both `/documents` and `/api/documents`.

- `POST /documents/upload` - upload a file and create a document record.
- `GET /documents` - list uploaded documents.
- `GET /documents/{document_id}` - fetch a single document record.
- `DELETE /documents/{document_id}` - delete the record and stored file.

Uploaded originals are saved under `UPLOAD_DIR`, which defaults to `storage/uploads`.
Uploads are parsed for supported text sources (`txt`, `md`, `csv`, `pdf`, `docx`, and `eml`) and chunked for search. Email attachments are inventoried; supported attachments (`txt`, `csv`, `tsv`, `md`, `log`, `docx`, `pdf`, and nested `eml`) are recursively text-extracted into the parent document text. Unsupported attachment types add processing warnings that appear in document detail views.

Blank or scanned PDFs first use normal PDF text extraction. If no text is available, OCR can run when configured:

```powershell
$env:OCR_ENABLED = "true"
$env:OCR_PDF_TO_TEXT_COMMAND = "your-ocr-command {input}"
```

The command must write extracted text to stdout. When OCR is not configured or fails, the document is marked `needs_ocr` with processing warnings.

## Matter And Custodian APIs

- `GET /api/matters` - list matters.
- `POST /api/matters` - create a matter.
- `GET /api/matters/{matter_id}` - fetch a matter.
- `PATCH /api/matters/{matter_id}` - update a matter.
- `GET /api/custodians` - list custodians.
- `POST /api/custodians` - create a custodian.
- `GET /api/custodians/{custodian_id}` - fetch a custodian.
- `PATCH /api/custodians/{custodian_id}` - update a custodian.

## Search API

- `POST /api/search` - search parsed document chunks and return citation-bearing results. Supports optional `matter_id`, `custodian_id`, `document_type`, `file_type`, `processing_status`, `date_from`, and `date_to` filters.
- `GET /api/search/saved` - list saved searches, optionally scoped by `matter_id`.
- `POST /api/search/saved` - save a query and filter set.
- `POST /api/search/saved/{saved_search_id}/run` - execute a saved search.

Search uses persisted chunk embeddings for local development. Set `QDRANT_ENABLED=true` to index chunks into Qdrant and query Qdrant first, with database-backed search as a fallback.
Metadata-filtered searches use local SQL-backed retrieval so filters are applied consistently. Saved search creation and execution create `saved_search.create` and `saved_search.run` audit events.

To run the Docker-backed Qdrant integration test locally, start Qdrant from the repository root and run the targeted test file:

```powershell
docker compose up -d qdrant
cd backend
$env:QDRANT_ENABLED = "true"
python -m pytest tests/test_qdrant_integration.py -q
```

The integration test seeds chunks through the upload API, verifies Qdrant indexing, hydrates Qdrant hits back into citation-bearing search results, and records local-versus-Qdrant comparison metrics during evaluation. If Qdrant is unavailable, the service falls back to local database search.

## AI Assistant API

- `POST /api/ai/answer` - answer a question from retrieved document chunks with citations, source snippets, and grounding signals.

The assistant uses local extractive grounded answers by default. Set `AI_PROVIDER=openai`, `AI_EXTERNAL_ENABLED=true`, `AI_MODEL`, and `OPENAI_API_KEY` to enable external model generation.

## Entity API

- `GET /api/entities` - list extracted entities with mention counts.
- `GET /api/entities/{entity_id}` - fetch an entity and its cited mentions.
- `GET /api/entities/{entity_id}/relationships` - list relationships connected to an entity.

Entity extraction runs during document ingestion for parsed text chunks. The first implementation uses deterministic rules for people, organizations, dates, money, legal references, locations, and email addresses.

## Graph API

- `GET /api/graph` - return visualization-ready graph nodes, edges, and metrics.
- `GET /api/graph/neighborhood/{entity_id}` - return a depth-limited entity neighborhood.
- `GET /api/graph/path` - return shortest paths between two entities.
- `GET /api/graph/metrics` - return graph-level counts, density, components, and top entities.

The graph is constructed from persisted entities, mentions, and relationships. It is scoped by optional matter and relationship filters.

## Analytics API

- `GET /api/analytics/snapshot` - return high-level document, entity, relationship, file type, and custodian counts.
- `GET /api/analytics/dashboard` - return chart-ready dashboard data for document timelines, file types, document classes, entity types, relationship types, custodians, and communication pairs.

Analytics are computed from persisted documents, entities, and relationships. The endpoints support optional `matter_id` filtering.

## Evaluation API

- `GET /api/evaluation/benchmarks` - list synthetic benchmark cases.
- `POST /api/evaluation/run` - run retrieval, answer, or combined benchmark checks with `task_type` set to `retrieval`, `answer`, or `all`.
- `GET /api/evaluation/metrics` - list persisted evaluation metric rows.
- `POST /api/evaluation/check-answer` - compare an answer against cited chunks and return grounding risk signals.

The first evaluation framework is deterministic and local. It does not call external AI providers, which keeps regression tests repeatable. Answer benchmarks measure expected-term coverage, citation validity, unsupported-term rate, hallucination risk, no-answer behavior, and pass/fail status.
When Qdrant is enabled, retrieval evaluation also records `qdrant_local_result_overlap`, `qdrant_local_top_result_match`, and `qdrant_result_count_delta` so ranking differences are visible in metric history.

## Audit API

- `GET /api/audit` - list audit events with optional `matter_id`, `document_id`, `event_actor`, `action`, `created_from`, and `created_to` filters.
- `GET /api/audit/export?format=csv|json` - export filtered audit events.
- `POST /api/audit/retention/purge` - delete audit events older than `AUDIT_RETENTION_DAYS`; admin role required when auth is enabled.

The platform records audit events for matter and custodian management, document upload/view/delete, search, AI answers, evaluation checks, permission denials, and ingestion failures. Set `AUDIT_RETENTION_DAYS` to control local retention; the default is 365 days.

## Authentication

Authentication is disabled by default for local development. Set `AUTH_ENABLED=true` to require an `X-API-Key` header on protected routes. API keys are matched to persisted `users.api_key_hash` records; each user has a role, and non-admin users must have `matter_memberships` rows for the matters they can access.

When auth is enabled, unscoped matter reads are limited to the actor's assigned matters. Cross-matter reads and writes return `403` and create `permission.denied` audit events. Document uploads require a `matter_id` when auth is enabled.

## Database

Set `DATABASE_URL` in `.env` for PostgreSQL. The default application setting uses SQLite for local development when PostgreSQL is not running.

```powershell
alembic upgrade head
```

The FastAPI app initializes tables on startup only when `APP_ENVIRONMENT=development` and `DATABASE_AUTO_CREATE_TABLES=true`. Use Alembic migrations for shared or production-style databases. Run `python ../scripts/check_migration_drift.py` from the repository root to verify model/migration alignment.

Backup, restore, and reset helpers live in `scripts/`; see `docs/OPERATIONS_DEPLOYMENT.md`.
