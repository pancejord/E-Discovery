# AI-Powered Litigation & eDiscovery Analytics Platform

Starter workspace for a legal analytics platform that ingests litigation and eDiscovery documents, extracts metadata and entities, supports AI-assisted search, and visualizes relationships across matters, people, organizations, and documents.

## Project Shape

- `backend/` - FastAPI service for ingestion, metadata extraction, search, analytics, and AI workflows.
- `frontend/` - Next.js app for review, search, dashboards, and investigation views.
- `data/` - Local-only sample, incoming, and processed document areas.
- `docs/` - Planning notes, architecture, roadmap, and product requirements.
- `scripts/` - Utility scripts for setup and local maintenance.

## First Milestone

Phase 1 focuses on the document processing foundation:

1. Upload documents into a matter workspace.
2. Parse basic text and file metadata.
3. Store normalized document records.
4. Expose document search and filtering endpoints.
5. Show document counts, file types, custodians, and timeline basics in the UI.

## Local Start

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Production build check:

```powershell
cd frontend
npm install
npm run build
```

Repeatable smoke checks:

```powershell
python scripts/smoke_check.py
python scripts/smoke_check.py --frontend
python scripts/smoke_check.py --synthetic-evaluation
```

CI runs backend tests, backend compile checks, Alembic migration checks, and the frontend production build. A manual CI option runs Docker-backed Qdrant integration checks.

Developer runtime notes, cleanup commands, task aliases, and the bundled Codex desktop runtime workaround are documented in `docs/DEVELOPER_ENVIRONMENT.md`.

## Docker Compose

App-only with SQLite:

```powershell
docker compose --profile app up --build
```

App with Postgres and Qdrant:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@postgres:5432/ediscovery"
$env:QDRANT_ENABLED="true"
docker compose --profile full up --build
```

Operational notes, environment variables, backup/restore commands, and health checks are documented in `docs/OPERATIONS_DEPLOYMENT.md`.

## Notes

Keep real client data out of the repo. Use `data/samples/` for synthetic or approved test material only.
