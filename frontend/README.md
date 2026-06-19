# Frontend

Next.js interface for the litigation analytics workspace.

## Run

```powershell
npm install
npm run dev
```

The app will run at `http://localhost:3000`.

## Pages

- `/` - investigation workspace with live matter metrics, matter/custodian setup, upload, search, and recent documents.
- `/assistant` - cited investigation assistant backed by `/api/ai/answer`.
- `/dashboard` - Plotly analytics dashboard backed by `/api/analytics/dashboard`.
- `/graph` - knowledge graph visualization backed by `/api/graph`, with matter, relationship, entity type, entity search, and confidence filters.
- `/documents/[documentId]` - source review page with metadata, processing notes, extracted text, entities, relationships, and citation chunks.
