# Phase 5 Changes

Date: 2026-06-11

## Purpose

Phase 5 turns the project analytics placeholder into a working analytics dashboard. The goal is to help litigation and eDiscovery teams scan document volume, document timelines, file and document type distributions, custodian activity, entity extraction patterns, relationship patterns, and communication pairs.

## Phase 4 Readiness Check

Phase 4 was verified before Phase 5 work began:

- Graph construction exists over persisted entities, mentions, and relationships.
- Graph APIs return visualization-ready nodes, edges, metrics, neighborhoods, and shortest paths.
- The frontend `/graph` page renders graph metrics and entity relationships.
- Phase 4 tests cover graph response data, metrics, neighborhoods, shortest paths, and validation.

Verification before Phase 5:

- `python -m pytest -q`: 6 tests passed.
- `python -m compileall -q app`: passed.
- Initial `npm run build` was blocked by a stale local Next.js file lock from the previous dev server. The process was stopped and the build was rerun successfully during Phase 5 verification.

## Phase 5 Implementation

The following capabilities were added:

- Analytics aggregation for document counts, entity counts, relationship counts, file type counts, and custodian counts.
- Timeline analytics using document dates when available and upload timestamps otherwise.
- Chart-ready distributions for file types, document types, entity types, relationship types, and top custodians.
- Communication analysis from `communicated_with` relationships.
- `/api/analytics/dashboard` endpoint for the full dashboard payload.
- `/api/analytics/snapshot` endpoint backed by real data instead of placeholder zeros.
- Plotly-powered frontend analytics dashboard at `/dashboard`.
- Dashboard navigation from the workspace landing page.

## Files Changed

- `backend/app/models/schemas.py`
  Change: Added analytics bucket, timeline point, communication metric, and dashboard response schemas.
  Purpose: Provide typed API contracts for Phase 5 dashboard data.

- `backend/app/services/analytics.py`
  Change: Added analytics aggregation service.
  Purpose: Keep dashboard calculations reusable and out of the FastAPI route layer.

- `backend/app/api/analytics.py`
  Change: Replaced placeholder snapshot behavior and added the dashboard endpoint.
  Purpose: Expose real analytics data through the backend API.

- `backend/tests/test_analytics.py`
  Change: Added analytics API tests with synthetic ingested documents and email communication.
  Purpose: Verify dashboard counts, timelines, distributions, custodians, and communication pairs.

- `frontend/lib/api.ts`
  Change: Added analytics response types and `getAnalyticsDashboard`.
  Purpose: Give the frontend typed access to `/api/analytics/dashboard`.

- `frontend/types/react-plotly.js.d.ts`
  Change: Added a minimal module declaration for `react-plotly.js`.
  Purpose: Allow TypeScript to build the dashboard component cleanly.

- `frontend/components/AnalyticsDashboardView.tsx`
  Change: Added the client-side analytics dashboard with Plotly charts and a communication table.
  Purpose: Deliver the Phase 5 analytics user experience.

- `frontend/app/dashboard/page.tsx`
  Change: Replaced the placeholder page with the analytics dashboard component.
  Purpose: Make `/dashboard` a working product surface.

- `frontend/app/page.tsx`
  Change: Added a dashboard link in the workspace header.
  Purpose: Make Phase 5 discoverable from the first screen.

- `backend/README.md`
  Change: Documented analytics API endpoints.
  Purpose: Help developers exercise the Phase 5 backend.

- `frontend/README.md`
  Change: Documented the dashboard page.
  Purpose: Help developers find the Phase 5 frontend view.

- `docs/CHANGE_LOG.md`
  Change: Added this Phase 5 project entry.
  Purpose: Maintain the project history in the existing change log.

- `docs/PHASE_5_CHANGES.md`
  Change: Added Phase 4 audit, Phase 5 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide the requested markdown record of changes and their purpose.

## Verification

- `python -m pytest -q`: 8 tests passed.
- `python -m compileall -q app`: passed.
- `npm run build`: passed.
- `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///./tmp_phase5_migration.db`: passed.
- Browser smoke test against `/dashboard` with temporary sample data: passed.

## Follow-Up Notes

- Analytics are currently computed dynamically from relational tables.
- Phase 6 can add regression tests for analytics quality and benchmark expected dashboard metrics from fixture datasets.
- A later UI pass can add matter selection once the frontend has matter management screens.
