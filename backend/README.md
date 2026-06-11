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
Uploads are parsed for supported text sources (`txt`, `md`, `csv`, `pdf`, `docx`, and `eml`) and chunked for search.

## Search API

- `POST /api/search` - search parsed document chunks and return citation-bearing results.

Search uses persisted chunk embeddings for local development. Set `QDRANT_ENABLED=true` to also index chunks into the configured Qdrant collection.

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

## Database

Set `DATABASE_URL` in `.env` for PostgreSQL. The default application setting uses SQLite for local development when PostgreSQL is not running.

```powershell
alembic upgrade head
```

The FastAPI app also initializes tables on startup for lightweight local development. Use Alembic migrations for shared or production-style databases.
