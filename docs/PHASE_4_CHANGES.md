# Phase 4 Changes

Date: 2026-06-11

## Purpose

Phase 4 adds the knowledge graph layer for the litigation and eDiscovery workspace. The goal is to turn persisted Phase 3 entities and relationships into queryable, visualization-ready graph data that can support entity neighborhoods, shortest paths, centrality-style review, and relationship exploration.

## Phase 3 Readiness Check

Phase 3 was verified before Phase 4 work began:

- Entities are persisted by matter, normalized name, and type.
- Entity mentions preserve document, chunk, offsets, and citations.
- Relationships are persisted with type, confidence, source, target, document, and evidence.
- Entity APIs list entities, return cited mentions, and show entity relationships.
- Alembic migration `0003_entities_relationships` applies cleanly.

Verification before Phase 4:

- `python -m pytest -q`: 4 tests passed.
- `python -m compileall -q app`: passed.
- `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///./tmp_phase4_audit.db`: passed.

## Phase 4 Implementation

The following capabilities were added:

- Dynamic graph construction from persisted entities, entity mentions, and relationships.
- Visualization-ready graph nodes and edges with labels, types, weights, confidence, evidence, and document ids.
- Graph metrics including node count, edge count, connected components, density, and top entities.
- Entity neighborhood queries with configurable depth and relationship filtering.
- Shortest-path queries between entities.
- A frontend `/graph` page with an SVG relationship network, metrics panel, selected entity panel, top entities list, refresh control, and relationship type filter.
- Local-development CORS support so the browser frontend can call the FastAPI backend.

## Files Changed

- `backend/app/models/schemas.py`
  Change: Added graph node, edge, metrics, graph response, and path response schemas.
  Purpose: Provide typed API responses for graph visualization and graph queries.

- `backend/app/services/knowledge_graph.py`
  Change: Added NetworkX-backed graph construction, edge aggregation, graph metrics, neighborhood queries, and shortest-path queries.
  Purpose: Implement Phase 4 graph behavior from existing relational entity and relationship data.

- `backend/app/api/graph.py`
  Change: Added `/api/graph`, `/api/graph/neighborhood/{entity_id}`, `/api/graph/path`, and `/api/graph/metrics`.
  Purpose: Expose graph construction and graph queries through FastAPI.

- `backend/app/main.py`
  Change: Registered the graph router and added local-development CORS middleware.
  Purpose: Make graph APIs available and callable from the browser frontend.

- `backend/tests/test_graph.py`
  Change: Added tests for graph response data, metrics, neighborhoods, shortest paths, and validation.
  Purpose: Verify Phase 4 behavior through the public API.

- `frontend/lib/api.ts`
  Change: Added graph response types and a `getKnowledgeGraph` API helper.
  Purpose: Give the frontend a typed way to call `/api/graph`.

- `frontend/components/KnowledgeGraphView.tsx`
  Change: Added a client-side SVG graph visualization with metrics, entity selection, top entities, refresh, and relationship filtering.
  Purpose: Deliver the Phase 4 relationship visualization experience.

- `frontend/app/graph/page.tsx`
  Change: Added the `/graph` page.
  Purpose: Make the knowledge graph visualization available in the Next.js app.

- `frontend/app/page.tsx`
  Change: Added a link to the graph page from the workspace header.
  Purpose: Make Phase 4 discoverable from the existing first screen.

- `backend/README.md`
  Change: Documented graph API endpoints.
  Purpose: Help developers exercise the Phase 4 backend.

- `frontend/README.md`
  Change: Documented the graph page.
  Purpose: Help developers find the Phase 4 frontend view.

- `docs/CHANGE_LOG.md`
  Change: Added this Phase 4 project entry.
  Purpose: Maintain the project history in the existing change log.

- `docs/PHASE_4_CHANGES.md`
  Change: Added Phase 3 audit, Phase 4 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide the requested markdown-style phase record.

## Verification

- `python -m pytest -q`: 6 tests passed.
- `python -m compileall -q app`: passed.
- `npm run build`: passed.
- `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///./tmp_phase4_migration.db`: passed.
- Browser smoke test against `/graph` with temporary sample data: passed.

## Follow-Up Notes

- The graph is dynamically built from relational data, not cached in separate graph tables.
- Phase 5 can reuse `/api/graph/metrics` and `/api/graph` for dashboard widgets.
- A later frontend pass can replace the radial SVG layout with a force-directed layout if the graph grows dense.
