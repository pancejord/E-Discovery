# Post-Build Remaining Work

Date: 2026-06-23

## Current Project State

The original `NEXT_BUILD_ORDER.md` steps 1 through 10 are complete at first-pass prototype level. The platform now has:

- Matter and custodian setup
- Upload, parsing, chunking, OCR signaling/execution hook, and attachment extraction
- Citation-bearing search, advanced filters, saved searches, and optional Qdrant retrieval
- Document source review with chunks, entities, relationships, processing notes, and OCR status
- Entity extraction, relationship persistence, knowledge graph visualization, and analytics dashboards
- Local cited AI answers, optional external OpenAI provider support, grounding checks, and evaluation metrics
- Audit review/export/retention purge
- Optional API-key authentication with users, roles, and matter memberships
- CI and local smoke checks

The remaining work is no longer about proving the basic product loop. It is about making the system safer, more scalable, more administrable, and more useful for real legal review.

## Progress Update

2026-06-23:

- Step 1 is complete for the current pass. `REMAINING_WORK.md`, `ROADMAP.md`, `NEXT_STEPS.md`, and `DATA_MODEL.md` now reflect the implemented product state instead of earlier phase assumptions.
- Step 2 is complete at first-pass prototype level. Admin APIs and an `/admin` frontend page now support role creation, user creation/update/deactivation, display-once API-key generation/rotation, and matter membership create/update/delete. Remaining production hardening belongs under Step 3 and Step 4.

2026-06-24:

- Step 3 is complete at first-pass hardening level. Bearer-token authentication is available behind `AUTH_BEARER_ENABLED`, users now carry organization and tenant metadata, actor context is copied into audit details, and `docs/PRODUCTION_IDENTITY_AND_AUDIT.md` documents local API-key mode versus production identity-provider mode.
- Step 4 is complete at first-pass hardening level. Audit rows now capture request IDs, client IP, user agent, route, method, response status, export manifests, request completion events, startup/manual retention purge events, OCR failure events, and vector indexing failure events.

2026-06-25:

- Step 5 is complete at first-pass production-processing level. Supported email attachments are now persisted as child documents, processing stages/errors are stored on documents, reprocess/retry endpoints rebuild extraction/chunking/indexing/entity stages, and lightweight HTML, RTF, XLSX, and ZIP extraction is available alongside the existing text/PDF/DOCX/EML handling.
- Step 6 is complete at first-pass review level. Document detail pages now support review status, privilege flag, tags, issue codes, reviewer notes, selected-chunk next/previous navigation, and highlighted search terms when opened from search results.
- Step 7 is complete at first-pass search-maturity level. Search now supports exact phrase and basic Boolean exclusion, review-coding filters, sender/recipient filters, result sorting, search diagnostics, saved-search update/delete/share behavior, and Qdrant payload filters for metadata-filtered vector search.
- Step 8 is complete at first-pass governance level. Assistant requests now support answer modes, per-matter external-AI policy settings, external-prompt redaction controls, and audit details for mode, provider policy, and redaction behavior.
- Step 9 is complete at first-pass evaluation-maturity level. Benchmarks now carry owner/triage metadata, extraction benchmark cases cover classification/date/entity/relationship/OCR-term signals, and evaluation summaries/trends are exposed through API and UI.
- Step 10 is complete at first-pass graph-review level. Entity extraction now runs behind a configurable provider interface with deterministic default and optional spaCy hook, relationships include richer deterministic types and confidence explanations, and entity merge/split APIs persist review/audit state.
- Step 11 is complete at first-pass scale level. Graph responses now support short-lived server caching plus entity limit/offset paging, and analytics dashboards support date/custodian filters plus CSV export.
- Step 12 is complete at first-pass persistence-hardening level. Startup `create_all()` is gated to development/local mode, Alembic drift checks are available in CI and scripts, common search/audit/evaluation indexes are migrated, and backup/restore/reset scripts are documented.
- Step 13 is complete at first-pass deployment-assets level. Backend and frontend Dockerfiles, Compose profiles, service health checks, environment reference docs, and structured request logging settings are now available.
- Step 14 is complete at first-pass frontend-structure level. Shared UI primitives, stronger global design tokens, dashboard table sorting/pagination, inline form validation, responsive polish, and a lightweight frontend UI smoke check are now available.
- Step 15 is complete at first-pass developer-environment level. Cleanup and task scripts, Node version pinning, bundled-runtime documentation, and root/frontend lockfile guidance are now in place.

## Recommended Build Order

### 1. Clean Up Planning And Product Documentation

Priority: highest

Why:

- Several older docs still describe earlier project phases or list work that is now complete.
- Future contributors need one accurate source of truth.

Work:

1. Update `docs/REMAINING_WORK.md` to retire completed steps 5 through 10.
2. Update `docs/ROADMAP.md` so it includes the implemented Phase 7/8-style work and current hardening phase.
3. Update `docs/NEXT_STEPS.md` and `docs/PHASE_7_PLAN.md`, which are now stale.
4. Update `docs/DATA_MODEL.md` with users, roles, matter memberships, audit logs, saved searches, document processing metadata, and evaluation details.
5. Decide whether phase-specific change files remain historical records only.

Done when:

- A new developer can read the docs and understand the current system without contradictory planning notes.

### 2. Add User, Role, And Matter Administration UI

Priority: highest

Why:

- Backend auth and matter permissions exist, but there is no UI to manage users, API keys, roles, or memberships.
- Matter isolation is only operationally useful if admins can manage access safely.

Work:

1. Add admin APIs for user create/update/deactivate, role assignment, API-key rotation, and matter membership management.
2. Add an admin frontend page for users and matter assignments.
3. Add key rotation and key display-once behavior.
4. Add tests for admin-only access, user deactivation, role changes, and membership changes.
5. Add audit events for user, key, role, and membership changes.

Done when:

- Admins can manage users and matter access without direct database edits.

### 3. Strengthen Authentication For Production Identity

Priority: high

Why:

- API-key auth is useful for local and prototype environments, but real deployments typically need SSO/OIDC, session handling, and organization-level policy.

Work:

1. Add an OIDC/SAML integration design.
2. Support bearer-token authentication behind a feature flag.
3. Add organization/tenant fields if multi-client deployment is expected.
4. Add request user context consistently to audit records.
5. Document local API-key mode versus production identity-provider mode.

Done when:

- The app can integrate with a production identity provider while preserving local development behavior.

### 4. Expand Audit Defensibility

Priority: high

Why:

- Audit rows exist, but legal workflows often need request context, retention automation, and defensible export controls.

Work:

1. Add request IDs, client IP, user agent, route/method, and response status to audit events.
2. Add scheduled audit retention rather than manual purge only.
3. Add audit events for vector indexing failures, OCR command failures, saved search deletion/update, export actions, and admin changes.
4. Add immutable export manifests with hash totals for audit exports.
5. Add tests for audit scoping and request metadata.

Done when:

- Audit logs explain who did what, from where, when, and with enough context for review.

### 5. Improve Document Processing For Real Productions

Priority: high

Why:

- Current parsing is useful but still limited for common eDiscovery formats and large productions.

Work:

1. Package and document a real OCR toolchain, such as OCRmyPDF/Tesseract or a managed local service.
2. Store attachment extraction as child document records when appropriate, not only appended parent text.
3. Add PST/MSG, XLSX, HTML, RTF, image, and common archive handling.
4. Add per-document processing stages: uploaded, extracted, OCR complete, indexed, entity extraction complete, failed.
5. Add retry/reprocess endpoints for failed extraction, OCR, indexing, and entity extraction.
6. Add upload progress and large-file limits.

Done when:

- Realistic legal productions can be processed with clear status, retries, and attachment lineage.

### 6. Improve Document Review UX

Priority: high

Why:

- Document detail pages expose source text and chunks, but reviewers need faster navigation and evidence handling.

Work:

1. Add highlighted search terms and selected citation highlighting in extracted text.
2. Add chunk navigation, next/previous hit controls, and long-document section navigation.
3. Add document tags, notes, issue codes, privilege flags, and review status.
4. Add document family/attachment navigation.
5. Add bulk review actions for search results.

Done when:

- Reviewers can move from search result to evidence to coding decision efficiently.

### 7. Mature Search And Retrieval

Priority: high

Why:

- Search works, but larger matters need richer filters, better ranking, and transparent query behavior.

Work:

1. Add Boolean keyword search and exact phrase search.
2. Add filters for tags, privilege/review status, sender/recipient, date source, family, and saved search owner.
3. Add saved search update/delete/share behavior.
4. Add result sorting by relevance, date, custodian, and document type.
5. Add hybrid ranking diagnostics showing keyword/vector/metadata contributions.
6. Add Qdrant payload filters for metadata-filtered vector search instead of falling back to local search.

Done when:

- Review teams can build repeatable review sets and understand why each result matched.

### 8. Make AI Assistant More Useful And Governed

Priority: medium-high

Why:

- The local assistant is deterministic and safe, but limited. External provider mode exists, but governance and evaluation need more maturity.

Work:

1. Add streaming responses for external providers.
2. Add multi-source synthesis with clearer claim-to-citation mapping.
3. Add answer modes: summary, chronology, issues list, contradiction check, privilege risk, and deposition prep.
4. Add provider-enabled manual evaluation scripts and optional model-assisted judging.
5. Add redaction controls before any external provider call.
6. Add per-matter AI policy settings.

Done when:

- AI workflows are useful for legal analysis while remaining configurable, cited, and measurable.

### 9. Expand Evaluation And Benchmark Coverage

Priority: medium-high

Why:

- Evaluation exists but is still synthetic and small.

Work:

1. Add more synthetic pleadings, orders, discovery responses, chat exports, spreadsheets, and distractor documents.
2. Add extraction benchmarks for entities, relationships, document dates, OCR text, and classification.
3. Add saved benchmark run summaries and trend charts.
4. Add failure triage notes and benchmark case ownership.
5. Add optional sanitized-real-data benchmark workflow after approval and redaction.

Done when:

- Retrieval, answer quality, extraction, classification, and OCR quality can be tracked over time.

### 10. Improve Entity And Relationship Extraction

Priority: medium

Why:

- Current extraction is deterministic and useful for demos, but legal documents need stronger NER, alias handling, and relationship typing.

Work:

1. Add spaCy or transformer-backed NER behind a configurable provider interface.
2. Add alias/normalization review UI for entity merge/split.
3. Add relationship types beyond co-mention and email communication.
4. Add confidence explanations and evidence snippets for each relationship.
5. Add entity-level audit events for merge/split/edit decisions.

Done when:

- The knowledge graph can support real investigative workflows instead of only exploratory visualization.

### 11. Scale Graph And Analytics

Priority: medium

Why:

- Graph and analytics are computed dynamically and rendered in-browser. That is fine for small matters but may strain larger productions.

Work:

1. Add cached graph projections or materialized analytics tables.
2. Add graph pagination, clustering expansion, or server-side subgraph queries.
3. Add canvas/WebGL rendering if SVG becomes slow for large graphs.
4. Add dashboard date and custodian filters.
5. Add analytics export for charts and tables.

Done when:

- Larger matters remain responsive and understandable.

### 12. Harden Database And Persistence

Priority: medium

Why:

- Alembic exists, but the app still calls `create_all()` on startup for convenience.

Work:

1. Gate startup `create_all()` to development mode or remove it from production startup.
2. Add migration drift checks to CI if practical.
3. Add database indexes for common search filters and audit queries.
4. Add backup/restore documentation.
5. Add seed/demo database reset commands.

Done when:

- Schema management is migration-driven and production-safe.

### 13. Add Operational Deployment Assets

Priority: medium

Why:

- Docker Compose starts databases, but there is no full deployment recipe for app services.

Work:

1. Add backend and frontend Dockerfiles.
2. Add Compose profiles for app-only, app+Postgres, app+Postgres+Qdrant.
3. Add health checks for backend, frontend, Postgres, and Qdrant.
4. Add environment variable reference docs.
5. Add production logging and structured log output.

Done when:

- A developer can run the full stack consistently from a clean machine.

### 14. Improve Frontend Structure And Design System

Priority: medium-low

Why:

- The UI is usable, but repeated controls and states are implemented page by page.

Work:

1. Extract shared components for page headers, filter panels, empty states, loading states, error states, metrics, and tables.
2. Add consistent table sorting/pagination.
3. Add form validation and inline field errors.
4. Add responsive polish for dense panels on mobile.
5. Add lightweight frontend tests for core interaction flows.

Done when:

- UI work becomes easier to extend without duplicating patterns.

### 15. Clean Generated Artifacts And Developer Environment Friction

Priority: medium-low

Why:

- Local commands can create `__pycache__`, `.pytest_cache`, `.next`, `node_modules`, and temporary SQLite databases.
- The current desktop shell has no plain `npm` on PATH, and pnpm requires build-script approval.

Work:

1. Add a cleanup script for generated caches and temporary databases.
2. Document the bundled runtime workaround used in this environment.
3. Decide whether root `package-lock.json` should remain, since the real frontend lockfile lives under `frontend/`.
4. Consider committing a `.nvmrc` or `.node-version`.
5. Add `make`, PowerShell, or Python task aliases for common workflows.

Done when:

- Contributors can run checks without leaving noisy local artifacts behind.

## Suggested Immediate Sprint

If only one near-term sprint is planned, do these first:

1. Refresh stale documentation and data model docs.
2. Add user/matter membership admin UI and API-key rotation.
3. Add request metadata and scheduled retention for audit logs.
4. Add document review coding: tags, notes, issue codes, privilege flags, and review status.
5. Add child-document attachment persistence and retry/reprocess workflows.

This sequence moves the prototype closer to a usable legal review product without destabilizing the core ingestion-search-AI loop that now works.

## Verification Baseline Before New Work

Before starting a new feature branch or hardening sprint, run:

```powershell
cd C:\Users\jpz2294\Desktop\E-Discovery-LegalSight
python scripts/smoke_check.py
```

For frontend work:

```powershell
cd frontend
npm install
npm run build
```

For Docker-backed vector checks:

```powershell
docker compose up -d qdrant
python scripts/smoke_check.py --qdrant
```
