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
