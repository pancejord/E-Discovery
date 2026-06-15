# Frontend

Next.js interface for the litigation analytics workspace.

## Run

```powershell
npm install
npm run dev
```

The app will run at `http://localhost:3000`.

## Pages

- `/` - investigation workspace landing view.
- `/assistant` - cited investigation assistant backed by `/api/ai/answer`.
- `/dashboard` - Plotly analytics dashboard backed by `/api/analytics/dashboard`.
- `/graph` - knowledge graph visualization backed by `/api/graph`.
