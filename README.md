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

## Notes

Keep real client data out of the repo. Use `data/samples/` for synthetic or approved test material only.
