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

## Database

Set `DATABASE_URL` in `.env` for PostgreSQL. The default application setting uses SQLite for local development when PostgreSQL is not running.

```powershell
alembic upgrade head
```

The FastAPI app also initializes tables on startup for lightweight local development. Use Alembic migrations for shared or production-style databases.
