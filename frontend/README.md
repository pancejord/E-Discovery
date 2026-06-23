# Frontend

Next.js interface for the litigation analytics workspace.

## Run

```powershell
npm install
npm run dev
```

The app will run at `http://localhost:3000`.

## Build Verification

```powershell
npm install
npm run build
```

Verified on 2026-06-21. The build covers `/`, `/assistant`, `/audit`, `/dashboard`, `/graph`, and `/documents/[documentId]`.

## Pages

- `/` - investigation workspace with live matter metrics, matter/custodian setup, upload, search, and recent documents.
- `/assistant` - cited investigation assistant backed by `/api/ai/answer`.
- `/audit` - audit review and export UI backed by `/api/audit`.
- `/dashboard` - Plotly analytics dashboard backed by `/api/analytics/dashboard`.
- `/graph` - knowledge graph visualization backed by `/api/graph`, with matter, relationship, entity type, entity search, and confidence filters.
- `/documents/[documentId]` - source review page with metadata, processing notes, extracted text, entities, relationships, and citation chunks.
