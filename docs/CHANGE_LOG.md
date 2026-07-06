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

## 2026-06-25 - Frontend Design System And Developer Cleanup

Area: Frontend, Developer Experience, Documentation

Goal: Complete post-build steps 14 and 15 with a more polished shared frontend UI foundation, inline validation, dashboard table controls, cleanup tooling, runtime docs, and task aliases.

Update: Added LegalSight branding to the frontend metadata and major page headers so the product name is visible throughout the review experience.

Update: Added `docs/PROJECT_INTENT_AND_AI.md` to explain LegalSight's product purpose, AI role, governance model, and production-readiness priorities.

Update: Refreshed the frontend visual design with a richer LegalSight color system, branded hero/header treatments, improved card shadows, colored metric accents, stronger buttons, polished tables, and brighter empty/result states.

Update: Added the LegalSight logo asset to the frontend, expanded the home header, removed the "LegalSight Workspace" eyebrow, and enriched the page background color treatment.

Update: Tuned the home layout with a smaller centered logo, centered quick navigation, expanded header spacing, a wider page frame for the matter setup column, and stronger page/card shadow depth.

### Files Changed

- `frontend/app/globals.css`, `frontend/components/ui.tsx`
  Change: Added shared design tokens and reusable page header, panel, metric, empty-state, and alert components.
  Purpose: Make the frontend more consistent, more appealing, and easier to extend.

- `frontend/app/page.tsx`
  Change: Added inline field validation errors for matter, custodian, upload, search, and saved-search workflows.
  Purpose: Give reviewers immediate, local feedback instead of only generic status messages.

- `frontend/components/AnalyticsDashboardView.tsx`
  Change: Moved the dashboard onto shared UI primitives and added sortable, paginated communication analysis.
  Purpose: Improve dense dashboard readability and make table interactions consistent.

- `frontend/scripts/ui-smoke.mjs`, `frontend/package.json`
  Change: Added a lightweight UI smoke check and package script.
  Purpose: Catch accidental removal of shared frontend patterns during future edits.

- `scripts/cleanup_workspace.py`, `scripts/tasks.ps1`, `.node-version`
  Change: Added generated-artifact cleanup, PowerShell task aliases, bundled-runtime fallbacks, and Node 22 pinning.
  Purpose: Reduce local development friction and keep verification runs from leaving noisy files behind.

- `docs/DEVELOPER_ENVIRONMENT.md`, `README.md`, `scripts/README.md`, `docs/POST_BUILD_REMAINING_WORK.md`, `docs/CHANGE_LOG.md`
  Change: Documented runtime expectations, Codex desktop workarounds, cleanup commands, task aliases, and Step 14/15 completion.
  Purpose: Keep project guidance aligned with the current development workflow.

- `package-lock.json`
  Change: Removed the empty root lockfile.
  Purpose: Avoid confusion because the real frontend lockfile lives at `frontend/package-lock.json`.

### Verification

- Ran `python -m compileall -q scripts`: passed.
- Ran `python scripts\cleanup_workspace.py --dry-run`: passed.
- Ran `pnpm --dir frontend test:ui` with bundled Node on `PATH`: UI smoke checks passed.
- Ran `pnpm --dir frontend build` with bundled Node on `PATH`: production build passed.
- Ran `.\scripts\tasks.ps1 frontend-ui`: task alias passed.
- Ran `python -m compileall -q backend\app scripts`: passed.
- Ran `python scripts\cleanup_workspace.py --include-dependencies`: removed generated `.next`, transient `pnpm-lock.yaml`, frontend `node_modules`, and Python bytecode.

### Follow-Up Notes

- The existing Next.js advisory for `next@15.1.2` remains a dependency-hardening follow-up.
- Docker remains unavailable in this desktop shell, so Docker verification was not run in this pass.

## 2026-06-25 - Persistence Hardening And Deployment Assets

Area: Backend, Infrastructure, CI, Documentation, Deployment

Goal: Complete post-build steps 12 and 13 with migration-driven production startup, drift checks, persistence scripts, Docker assets, Compose profiles, health checks, environment docs, and structured logging.

### Files Changed

- `backend/app/core/config.py`, `backend/app/database.py`, `backend/app/main.py`
  Change: Added environment/table-creation gates, structured request logging settings, and JSON request log support.
  Purpose: Make production startup migration-driven and logs deployment-friendly.

- `backend/alembic/versions/0014_persistence_hardening_indexes.py`, `backend/alembic/versions/0015_migration_drift_alignment.py`, `backend/app/models/document.py`, `backend/app/models/audit_log.py`, `backend/app/models/evaluation.py`, `backend/app/models/relationship.py`, `backend/alembic/env.py`
  Change: Added common composite indexes, aligned historical unique/nullability drift, and made Alembic metadata imports explicit.
  Purpose: Improve query performance and make migration drift checks reliable.

- `scripts/check_migration_drift.py`, `scripts/backup_database.py`, `scripts/restore_database.py`, `scripts/reset_demo_database.py`, `scripts/smoke_check.py`
  Change: Added migration drift, backup, restore, reset, and smoke-check improvements.
  Purpose: Give contributors repeatable persistence operations.

- `.github/workflows/ci.yml`
  Change: Added migration drift check to CI.
  Purpose: Fail model/migration drift before it reaches shared environments.

- `backend/Dockerfile`, `backend/docker-entrypoint.sh`, `frontend/Dockerfile`, `docker-compose.yml`, `.dockerignore`, `backend/.dockerignore`, `frontend/.dockerignore`
  Change: Added app service images, startup migration entrypoint, Compose profiles, volumes, ports, and health checks.
  Purpose: Let developers run app-only, app+Postgres, or full app+Postgres+Qdrant stacks.

- `.env.example`, `backend/.env.example`, `docs/OPERATIONS_DEPLOYMENT.md`, `README.md`, `backend/README.md`, `scripts/README.md`, `docs/POST_BUILD_REMAINING_WORK.md`, `docs/CHANGE_LOG.md`
  Change: Documented settings, Compose profiles, health checks, backup/restore/reset commands, and Step 12/13 completion status.
  Purpose: Keep operational guidance aligned with implementation.

- `backend/tests/test_health.py`
  Change: Added tests for production-gated startup table creation.
  Purpose: Prevent `create_all()` from becoming unconditional again.

### Verification

- Ran `python -m pytest tests\test_health.py -q`: 3 tests passed.
- Ran `python -m pytest -q`: 44 tests passed, 1 skipped.
- Ran `python -m compileall -q app ..\scripts`: passed.
- Ran `python scripts\check_migration_drift.py`: Alembic upgrade plus `alembic check` passed with no new upgrade operations detected.
- Ran `pnpm build`: passed.

### Follow-Up Notes

- Docker is not installed in this desktop shell, so `docker compose config` and image builds could not be executed locally in this pass.
- The Next.js security advisory for `next@15.1.2` remains a dependency-hardening item.

## 2026-06-25 - Entity Review And Graph Analytics Scale

Area: Backend, Frontend, Entity Extraction, Graph, Analytics, Documentation

Goal: Complete post-build steps 10 and 11 with configurable entity extraction, entity review workflows, richer relationship evidence, graph pagination/cache, analytics filters, and analytics export.

### Files Changed

- `backend/app/core/config.py`
  Change: Added entity extraction provider settings, spaCy model setting, and graph cache TTL.
  Purpose: Make extraction and graph caching configurable.

- `backend/app/models/entity.py`, `backend/app/models/relationship.py`, `backend/alembic/versions/0013_entity_review_graph_analytics_scale.py`
  Change: Added entity alias/review/provider fields and relationship confidence explanations.
  Purpose: Persist merge/split review state and explain relationship confidence.

- `backend/app/services/entity_extraction.py`
  Change: Added provider abstraction with deterministic default and optional spaCy hook; added relationship types for associations, money, legal references, locations, and dated events.
  Purpose: Mature extraction while keeping local deterministic behavior stable.

- `backend/app/api/entities.py`, `backend/app/api/documents.py`, `backend/app/models/schemas.py`
  Change: Exposed entity review metadata, relationship confidence explanations, and merge/split endpoints with audit events.
  Purpose: Support alias normalization review workflows.

- `backend/app/services/knowledge_graph.py`, `backend/app/api/graph.py`
  Change: Added short-lived graph response caching and entity limit/offset paging.
  Purpose: Keep large graph responses more manageable.

- `backend/app/services/analytics.py`, `backend/app/api/analytics.py`
  Change: Added custodian/date filters and CSV export for analytics dashboards.
  Purpose: Let reviewers focus and export chart/table data.

- `frontend/lib/api.ts`, `frontend/components/KnowledgeGraphView.tsx`, `frontend/components/AnalyticsDashboardView.tsx`, `frontend/app/page.tsx`
  Change: Added graph paging controls, relationship confidence explanations, dashboard filters, and analytics export link.
  Purpose: Surface scale controls in the review UI.

- `backend/tests/test_graph.py`, `backend/tests/test_analytics.py`
  Change: Added coverage for richer relationships, graph paging, entity merge/split, analytics filtering, and CSV export.
  Purpose: Prevent regressions in entity review and scale workflows.

- `docs/DATA_MODEL.md`, `docs/POST_BUILD_REMAINING_WORK.md`, `docs/CHANGE_LOG.md`
  Change: Documented entity review fields, relationship explanations, and Step 10/11 completion status.
  Purpose: Keep the project record aligned with implementation.

### Verification

- Ran `python -m pytest tests\test_graph.py tests\test_analytics.py -q`: 5 tests passed.
- Ran `python -m pytest -q`: 42 tests passed, 1 skipped.
- Ran `python -m compileall -q app`: passed.
- Ran `python -m alembic upgrade head` against a temporary SQLite database: passed through `0013_entity_review_graph_analytics_scale`.
- Ran `pnpm build`: passed; `/graph` and `/dashboard` compiled with the updated controls.

### Follow-Up Notes

- The spaCy provider is optional and falls back to deterministic extraction when the model is not installed.
- Graph rendering is still SVG, but responses can now be paged server-side. Canvas/WebGL remains a future rendering upgrade if graph size demands it.
- The Next.js security advisory for `next@15.1.2` remains a dependency-hardening item.

## 2026-06-25 - AI Governance And Evaluation Maturity

Area: Backend, Frontend, AI Assistant, Evaluation, Documentation

Goal: Complete post-build steps 8 and 9 with governed assistant modes, per-matter AI policy, prompt redaction controls, richer benchmark metadata, extraction benchmarks, and evaluation summary/trend views.

### Files Changed

- `backend/app/models/matter.py`, `backend/alembic/versions/0012_ai_governance_evaluation_maturity.py`
  Change: Added per-matter AI external-provider permission, redaction requirement, and allowed answer modes.
  Purpose: Let matters govern whether and how AI provider workflows can run.

- `backend/app/models/schemas.py`, `backend/app/api/matters.py`
  Change: Added AI policy fields to matter schemas and JSON serialization for allowed modes.
  Purpose: Expose matter AI governance through the existing matter API.

- `backend/app/services/ai.py`, `backend/app/api/ai.py`
  Change: Added answer modes, provider-policy enforcement, external prompt redaction, policy metadata, and richer audit details.
  Purpose: Make assistant answers more useful while preserving cited, governed behavior.

- `backend/app/services/evaluation.py`, `backend/app/api/evaluation.py`
  Change: Added extraction benchmark execution plus summary and trend endpoints.
  Purpose: Track retrieval, answer, extraction, classification, OCR-term, and benchmark quality over time.

- `data/samples/evaluation_benchmarks.json`
  Change: Added benchmark owner/triage metadata and extraction benchmark cases.
  Purpose: Make benchmark failures easier to assign and diagnose.

- `frontend/lib/api.ts`, `frontend/components/InvestigationAssistantView.tsx`, `frontend/app/evaluation/page.tsx`
  Change: Added assistant mode/redaction controls, policy status, extraction evaluation runs, metric summaries, trend points, and triage metadata display.
  Purpose: Surface governance and evaluation maturity in the UI.

- `backend/tests/test_ai.py`, `backend/tests/test_evaluation.py`
  Change: Added coverage for AI policy/redaction and extraction summaries/trends.
  Purpose: Prevent regressions in governed assistant and evaluation workflows.

- `docs/DATA_MODEL.md`, `docs/EVALUATION_DATASET_STRATEGY.md`, `docs/POST_BUILD_REMAINING_WORK.md`, `docs/CHANGE_LOG.md`
  Change: Documented matter AI policy fields, expanded evaluation coverage, and Step 8/9 completion status.
  Purpose: Keep the project record aligned with implementation.

### Verification

- Ran `python -m pytest tests\test_ai.py tests\test_evaluation.py -q`: 11 tests passed.
- Ran `python -m pytest -q`: 41 tests passed, 1 skipped.
- Ran `python -m compileall -q app`: passed.
- Ran `python -m alembic upgrade head` against a temporary SQLite database: passed through `0012_ai_governance_evaluation_maturity`.
- Ran `pnpm build`: passed; `/assistant` and `/evaluation` compiled with the updated controls.

### Follow-Up Notes

- Streaming provider responses and model-assisted judging are not yet fully implemented; this pass lays the policy, mode, redaction, and metric surfaces needed for them.
- Per-matter AI policy is currently API-backed; a fuller admin UI for editing those settings can be added in a later hardening pass.
- The Next.js security advisory for `next@15.1.2` remains a dependency-hardening item.

## 2026-06-25 - Document Processing For Real Productions

Area: Backend, Frontend, Document Processing, Documentation

Goal: Complete post-build step 5 with child-document attachment persistence, processing stages and errors, reprocess/retry endpoints, broader lightweight extraction, and operational notes for OCR and reprocessing.

### Files Changed

- `backend/app/models/document.py`, `backend/alembic/versions/0011_document_families_reprocessing.py`
  Change: Added parent/child document fields, attachment filename, processing stages, and processing error.
  Purpose: Persist document family lineage and processing state.

- `backend/app/services/text_extraction.py`
  Change: Added structured attachment extraction plus HTML, RTF, XLSX, and ZIP text extraction.
  Purpose: Cover more common production formats and provide payloads for child attachment documents.

- `backend/app/services/ingestion.py`
  Change: Refactored ingestion into reusable stages, persisted supported email attachments as child documents, added reprocess support, and tracked stage/error state.
  Purpose: Make ingestion retryable and preserve attachment lineage.

- `backend/app/api/documents.py`, `backend/app/models/schemas.py`
  Change: Exposed family/stage fields and added `reprocess` and `retry/{stage}` endpoints.
  Purpose: Let reviewers and admins inspect and rerun processing without direct database edits.

- `frontend/lib/api.ts`, `frontend/app/documents/[documentId]/page.tsx`
  Change: Added document family display, processing stages/errors, and reprocess controls.
  Purpose: Surface production-processing state in the review UI.

- `backend/tests/test_document_processing.py`
  Change: Added coverage for child attachments, reprocessing, and HTML/RTF/XLSX/ZIP extraction.
  Purpose: Prevent regressions in document-processing workflows.

- `docs/DATA_MODEL.md`, `docs/DOCUMENT_PROCESSING_OPERATIONS.md`, `docs/POST_BUILD_REMAINING_WORK.md`, `docs/CHANGE_LOG.md`
  Change: Documented new model fields, processing operations, and Step 5 completion status.
  Purpose: Keep the project record aligned with implementation.

### Verification

- Ran `python -m pytest tests\test_document_processing.py tests\test_documents.py -q`: 10 tests passed.
- Ran `python -m pytest -q`: 38 tests passed, 1 skipped.
- Ran `python -m compileall -q app`: passed.
- Ran `python -m alembic upgrade head` against a temporary SQLite database: passed through `0011_document_families_reprocessing`.
- Ran direct Next build with bundled Node after pnpm install populated dependencies: passed.

### Follow-Up Notes

- OCR remains command-configured; `docs/DOCUMENT_PROCESSING_OPERATIONS.md` records the expected toolchain contract.
- PST/MSG, standalone image OCR, independent archive-child persistence, and richer upload progress/large-file UX remain future production-hardening work.
- The Next.js security advisory for `next@15.1.2` remains a dependency-hardening item.

## 2026-06-25 - Document Review Coding And Search Maturity

Area: Backend, Frontend, Search, Document Review

Goal: Complete post-build steps 6 and 7 with review coding, source highlighting/navigation, richer search filters, saved-search management, and search diagnostics.

### Files Changed

- `backend/app/models/document.py`, `backend/app/models/saved_search.py`, `backend/alembic/versions/0010_review_coding_search_maturity.py`
  Change: Added document review coding fields and saved-search sharing/update metadata.
  Purpose: Persist reviewer decisions and repeatable review-set management.

- `backend/app/models/schemas.py`
  Change: Added document coding, search diagnostics, review filter, sort, and saved-search update/share schemas.
  Purpose: Expose typed contracts for review and search maturity workflows.

- `backend/app/api/documents.py`
  Change: Added document coding update endpoint and explicit document serializers for tags, issue codes, privilege flag, and review status.
  Purpose: Let reviewers code documents without direct database edits.

- `backend/app/services/search.py`, `backend/app/services/vector_store.py`, `backend/app/api/search.py`
  Change: Added phrase/exclusion parsing, review-coding filters, sender/recipient filters, sorting, diagnostics, saved-search update/delete/share, and Qdrant payload filters.
  Purpose: Make search more repeatable, explainable, and useful for review-set workflows.

- `frontend/lib/api.ts`, `frontend/app/page.tsx`, `frontend/app/documents/[documentId]/page.tsx`
  Change: Added review coding controls, search-result highlighting, chunk previous/next navigation, expanded search filters, result diagnostics, and saved-search management controls.
  Purpose: Give reviewers faster evidence navigation and practical coding/search controls in the UI.

- `backend/tests/test_search_filters_saved_searches.py`
  Change: Added coverage for coding updates, phrase/exclusion search, review filters, diagnostics, saved-search update/delete/share, and audit events.
  Purpose: Prevent regressions in the new review/search workflows.

- `docs/DATA_MODEL.md`, `docs/POST_BUILD_REMAINING_WORK.md`
  Change: Documented new fields and marked steps 6 and 7 complete at first-pass level.
  Purpose: Keep the project record aligned with implementation.

### Verification

- Ran `python -m pytest tests/test_search_filters_saved_searches.py tests/test_documents.py -q`: 6 tests passed.
- Ran `python -m pytest -q`: 36 tests passed, 1 skipped.
- Ran `python -m compileall -q app`: passed.
- Ran `python -m alembic upgrade head` against a temporary SQLite database: passed through `0010_review_coding_search_maturity`.
- Ran direct Next build with bundled Node after pnpm install populated dependencies: passed.

### Follow-Up Notes

- Search now supports exact quoted phrases and `NOT` exclusions. Full grouped Boolean logic can be added later if review teams need complex legal-search syntax.
- The Next.js security advisory for `next@15.1.2` remains a dependency-hardening item.

## 2026-06-24 - Production Identity And Audit Defensibility

Area: Backend, Frontend, Documentation

Goal: Complete post-build steps 3 and 4 with bearer-token auth support, tenant-aware actor context, request metadata on audit events, retention automation, and defensible audit exports.

### Files Changed

- `backend/app/core/config.py`, `.env.example`, `backend/.env.example`
  Change: Added `AUTH_BEARER_ENABLED` and `AUDIT_PURGE_ON_STARTUP` settings.
  Purpose: Allow bearer-token auth and scheduled audit retention to be enabled behind explicit flags.

- `backend/app/core/auth.py`
  Change: Added optional `Authorization: Bearer` credential resolution and tenant/organization fields on `Actor`.
  Purpose: Prepare the auth layer for production identity gateways while preserving local API-key behavior.

- `backend/app/models/user.py`, `backend/app/models/audit_log.py`, `backend/alembic/versions/0009_identity_audit_context.py`
  Change: Added user `organization` and `tenant_id` fields plus audit request metadata columns.
  Purpose: Persist identity context and request context in relational records.

- `backend/app/services/audit.py`, `backend/app/main.py`
  Change: Added request audit context, automatic `request.completed` events, actor context enrichment, and optional startup retention purge.
  Purpose: Make audit rows explain who did what, from where, and under which request.

- `backend/app/api/audit.py`
  Change: Added request metadata filters, export manifests, `audit.export`, and manual retention purge audit events.
  Purpose: Improve defensibility and traceability of audit review/export workflows.

- `backend/app/services/ingestion.py`
  Change: Added audit events for OCR failures and vector indexing failures.
  Purpose: Surface lower-level processing failures in the audit trail.

- `backend/app/api/admin.py`, `backend/app/models/schemas.py`
  Change: Added tenant and organization fields to admin user contracts.
  Purpose: Let admins maintain identity metadata.

- `frontend/lib/api.ts`, `frontend/app/admin/page.tsx`, `frontend/app/audit/page.tsx`
  Change: Added tenant/organization user fields and audit request metadata filters/table columns.
  Purpose: Make the new backend controls visible in the UI.

- `docs/PRODUCTION_IDENTITY_AND_AUDIT.md`, `docs/DATA_MODEL.md`, `docs/POST_BUILD_REMAINING_WORK.md`
  Change: Documented identity modes, audit metadata, export manifests, retention behavior, and step completion.
  Purpose: Keep project guidance aligned with the hardening work.

- `backend/tests/test_workspace_management.py`
  Change: Added coverage for bearer auth, actor context, request metadata, response-status events, and audit export manifests.
  Purpose: Prevent regressions in auth and audit defensibility behavior.

### Verification

- Ran `python -m pytest tests/test_workspace_management.py tests/test_admin.py -q`: 6 tests passed.
- Ran `python -m pytest -q`: 35 tests passed, 1 skipped.
- Ran `python -m compileall -q app`: passed.
- Ran `python -m alembic upgrade head` against a temporary SQLite database: passed through `0009_identity_audit_context`.
- Ran direct Next build with bundled Node after pnpm install populated dependencies: passed.

### Follow-Up Notes

- Bearer-token mode currently resolves tokens against stored user API-key hashes. A future OIDC/SAML implementation should validate provider JWTs and map claims into the same `Actor` shape.

## 2026-06-23 - Documentation Refresh And Admin Management

Area: Backend, Frontend, Documentation

Goal: Start the post-build backlog by refreshing stale planning/data docs and adding first-pass administration for users, roles, API keys, and matter assignments.

### Files Changed

- `backend/app/core/auth.py`
  Change: Added a reusable `require_admin` guard.
  Purpose: Keep admin-only API access consistent.

- `backend/app/api/admin.py`
  Change: Added admin endpoints for role list/create, user list/create/update/deactivate, API-key rotation, and matter membership list/create/update/delete.
  Purpose: Let administrators manage local users and matter access without direct database edits.

- `backend/app/models/schemas.py`
  Change: Added admin role, user, API-key rotation, and matter membership schemas.
  Purpose: Provide typed contracts for the new admin endpoints and frontend.

- `backend/app/main.py`
  Change: Registered the admin router under `/api/admin`.
  Purpose: Expose admin management APIs.

- `backend/tests/test_admin.py`
  Change: Added tests for admin lifecycle behavior, key rotation, user deactivation, memberships, audit events, and non-admin denial.
  Purpose: Prevent regressions in access-management behavior.

- `frontend/lib/api.ts`
  Change: Added typed admin API client functions and types.
  Purpose: Connect the Next.js UI to the admin backend.

- `frontend/app/admin/page.tsx`
  Change: Added the admin page for role creation, user creation/update/deactivation, API-key rotation, and matter assignment management.
  Purpose: Make matter isolation operationally manageable from the UI.

- `frontend/app/page.tsx`
  Change: Added an Admin navigation link.
  Purpose: Make the new admin surface discoverable.

- `docs/REMAINING_WORK.md`, `docs/ROADMAP.md`, `docs/NEXT_STEPS.md`, `docs/DATA_MODEL.md`, `docs/POST_BUILD_REMAINING_WORK.md`
  Change: Replaced stale phase/backlog content with current system status, current data model details, and progress notes for post-build steps 1 and 2.
  Purpose: Keep the project docs aligned with the actual implementation.

### Verification

- Ran `python -m pytest tests/test_admin.py -q`: 2 tests passed.
- Ran `python -m pytest -q`: 33 tests passed, 1 skipped.
- Ran `python -m compileall -q app`: passed.
- Ran direct Next build with bundled Node after pnpm install populated dependencies: passed.

### Follow-Up Notes

- The admin UI assumes the current local API-key mode. Production identity-provider integration remains a separate hardening step.

## 2026-06-23 - Dense Graph Layout And CI Smoke Checks

Area: Frontend, CI, Scripts

Goal: Complete build-order steps 9 and 10 with a denser graph layout and repeatable checks.

### Files Changed

- `frontend/components/KnowledgeGraphView.tsx`
  Change: Replaced the radial layout with a deterministic force/cluster positioner, added collision handling, link attraction, selected-neighborhood emphasis, and stable bounds.
  Purpose: Make larger relationship graphs more navigable while preserving existing filters and relationship review.

- `.github/workflows/ci.yml`
  Change: Added backend, frontend, and optional Docker-backed Qdrant smoke jobs.
  Purpose: Verify backend tests, compile checks, migrations, frontend builds, and service-backed vector behavior in CI.

- `scripts/smoke_check.py`, `scripts/README.md`
  Change: Added a local smoke runner for backend tests, compile checks, migrations, optional frontend build, optional synthetic evaluation, and optional Qdrant integration tests.
  Purpose: Make repeatable local verification easy without remembering several separate commands.

- `README.md`, `docs/NEXT_BUILD_ORDER.md`
  Change: Documented smoke checks, CI behavior, and step 9/10 completion status.
  Purpose: Keep project guidance aligned with the final build-order work.

### Verification

- Ran `python scripts/smoke_check.py`: 31 tests passed, 1 skipped; backend compile passed; Alembic upgraded through head.
- Ran direct Next build with bundled Node after pnpm install populated dependencies: passed.

## 2026-06-23 - OCR, Attachment Extraction, And Saved Searches

Area: Backend, Frontend, Search, Document Processing

Goal: Complete build-order steps 7 and 8 with optional OCR execution, deeper email attachment extraction, advanced search filters, and saved search workflows.

### Files Changed

- `backend/app/services/text_extraction.py`, `backend/app/core/config.py`, `backend/.env.example`
  Change: Added optional command-based PDF OCR and recursive supported attachment extraction for EML attachments.
  Purpose: Let scanned PDFs produce searchable text when OCR tooling is configured and make supported binary attachments searchable.

- `backend/app/services/search.py`, `backend/app/api/search.py`, `backend/app/models/schemas.py`
  Change: Added custodian, document type, file type, status, and document date filters; added saved search endpoints.
  Purpose: Support repeatable, narrowed eDiscovery searches.

- `backend/app/models/saved_search.py`, `backend/app/models/__init__.py`, `backend/app/database.py`, `backend/alembic/versions/0008_saved_searches.py`
  Change: Added persisted saved searches with query, filters, actor, and matter scope.
  Purpose: Store reusable review searches in relational persistence.

- `frontend/lib/api.ts`, `frontend/app/page.tsx`
  Change: Added typed saved-search APIs and workspace controls for advanced filters, saving, and running saved searches.
  Purpose: Let reviewers create and rerun filtered searches without raw API calls.

- `backend/tests/test_document_processing.py`, `backend/tests/test_search_filters_saved_searches.py`
  Change: Added coverage for OCR execution, DOCX attachment extraction, metadata-filtered search, saved search execution, and audit events.
  Purpose: Prevent regressions in the new processing and review workflows.

- `backend/README.md`, `frontend/README.md`, `docs/NEXT_BUILD_ORDER.md`
  Change: Documented OCR settings, attachment extraction behavior, saved search endpoints/UI, and step 7/8 completion status.
  Purpose: Keep developer guidance aligned with the implementation.

### Verification

- Ran `python -m pytest tests/test_document_processing.py tests/test_search_filters_saved_searches.py -q`: 7 tests passed.
- Ran `python -m pytest -q`: 31 tests passed, 1 skipped.
- Ran `python -m compileall -q app`: passed.
- Ran direct Next build with bundled Node after pnpm install populated dependencies: passed.

## 2026-06-23 - Qdrant Integration And Evaluation Dashboard

Area: Backend, Frontend, Evaluation

Goal: Complete build-order steps 5 and 6 by proving Qdrant-backed search behavior and exposing evaluation workflows in the UI.

### Files Changed

- `backend/app/services/vector_store.py`
  Change: Added Qdrant matter-list filtering and limit handling for scoped searches.
  Purpose: Let auth-scoped unfiltered searches use Qdrant without leaking cross-matter results.

- `backend/app/services/search.py`
  Change: Added explicit `auto`, `local`, and `qdrant` backend selection.
  Purpose: Support fallback behavior and local-versus-Qdrant evaluation comparisons.

- `backend/app/services/evaluation.py`, `backend/app/models/schemas.py`
  Change: Added metric details to API responses and persisted Qdrant comparison metrics when Qdrant is enabled.
  Purpose: Make ranking differences and failed benchmark context visible to reviewers.

- `backend/tests/test_qdrant_integration.py`
  Change: Added fallback, scoped Qdrant search, and Docker-backed Qdrant indexing/search/evaluation coverage.
  Purpose: Verify Qdrant works end-to-end locally while keeping normal test runs clean when Qdrant is unavailable.

- `frontend/lib/api.ts`, `frontend/app/evaluation/page.tsx`, `frontend/app/page.tsx`
  Change: Added evaluation API client methods, a benchmark dashboard, and navigation.
  Purpose: Let reviewers run retrieval, answer, or combined evaluations and inspect quality metrics from the frontend.

- `backend/README.md`, `frontend/README.md`, `docs/NEXT_BUILD_ORDER.md`
  Change: Documented Qdrant test commands, evaluation UI, and step 5/6 completion status.
  Purpose: Keep build and verification guidance aligned with the implementation.

### Verification

- Pending in this shell: project Python dependencies, npm, and Docker CLI are not on PATH.
- Structural verification performed by reviewing step 1-4 code paths before implementation.

## 2026-06-19 - Frontend Product Pass

Area: Frontend

Goal: Complete the remaining frontend product checklist for live metrics, search review, graph usability, and UI states.

### Files Changed

- `frontend/app/page.tsx`
  Change: Improved workspace loading/error states, search empty states, upload status, and search result metadata.
  Purpose: Make the main workspace usable as an operational review screen.

- `frontend/components/KnowledgeGraphView.tsx`
  Change: Added entity search, entity type filter, minimum confidence filter, filtered graph counts, selected relationship review, and document links.
  Purpose: Make graph exploration more useful as the graph grows.

- `frontend/components/AnalyticsDashboardView.tsx`
  Change: Added empty chart states for matters without data.
  Purpose: Avoid blank chart panels and clarify empty datasets.

- `frontend/components/InvestigationAssistantView.tsx`
  Change: Added clearer matter-load errors and answer-generation loading state.
  Purpose: Make assistant states consistent with the rest of the app.

- `frontend/lib/api.ts`
  Change: Added minimum-confidence support for graph requests.
  Purpose: Let the graph UI request filtered relationship data from the backend.

- `docs/REMAINING_WORK.md`
  Change: Marked frontend product items as implemented or first-pass implemented.
  Purpose: Keep the current product backlog accurate.

### Verification

- Frontend build is pending local Node package tooling.

## 2026-06-19 - Document Processing Hardening

Area: Backend Document Processing

Goal: Improve parsing, classification, OCR signaling, attachment handling, date normalization, and entity deduplication.

### Files Changed

- `backend/app/services/text_extraction.py`
  Change: Added safer PDF extraction, OCR recommendation for blank PDFs, DOCX table extraction, EML attachment inventory/text extraction, richer classification, and UTC date normalization.
  Purpose: Make upload processing more transparent and useful for legal review.

- `backend/app/models/document.py`, `backend/app/models/schemas.py`, `backend/app/api/documents.py`, `backend/app/services/ingestion.py`
  Change: Added extraction warnings, attachment names, and OCR status to persisted documents and detail responses.
  Purpose: Surface parsing limitations and attachment context to reviewers.

- `backend/alembic/versions/0006_document_processing_metadata.py`
  Change: Added migration for processing metadata fields.
  Purpose: Version the document schema changes.

- `backend/app/services/entity_extraction.py`
  Change: Added organization suffix normalization and cleaner person normalization.
  Purpose: Improve alias deduplication for deterministic entity extraction.

- `frontend/lib/api.ts`, `frontend/app/documents/[documentId]/page.tsx`
  Change: Displayed OCR status, extraction warnings, and attachment names on document source pages.
  Purpose: Make processing metadata visible in the review UI.

- `backend/tests/test_document_processing.py`
  Change: Added tests for EML attachments, UTC date normalization, richer classification, alias deduplication, and OCR signaling.
  Purpose: Prevent regressions in the document-processing pipeline.

- `docs/REMAINING_WORK.md`
  Change: Marked document-processing work as first-pass implemented and listed remaining hardening work.
  Purpose: Keep planning status current.

### Verification

- Ran `python -m pytest tests/test_document_processing.py -q`: 3 tests passed.

## 2026-06-19 - AI Evaluation Dataset Strategy

Area: AI Evaluation and Sample Data

Goal: Move evaluation from a hardcoded toy benchmark toward a safer synthetic-dataset workflow and start tracking live assistant answer quality.

### Files Changed

- `docs/EVALUATION_DATASET_STRATEGY.md`
  Change: Added guidance for synthetic-first evaluation data.
  Purpose: Establish a safe route before using any real or client-derived material.

- `data/samples/evaluation_benchmarks.json`
  Change: Expanded the benchmark fixture into multiple datasets with retrieval, answer, and negative cases.
  Purpose: Let benchmark cases grow without editing Python code.

- `data/samples/synthetic_mixed_production.json`
  Change: Added synthetic source documents for the richer mixed-production benchmark.
  Purpose: Provide stable legal-domain evaluation material with no real client data.

- `scripts/seed_synthetic_production.py`, `scripts/README.md`
  Change: Added scripts to load the synthetic production and run synthetic evaluation.
  Purpose: Make local evaluation/demo seeding and benchmark execution repeatable.

- `backend/app/services/evaluation.py`
  Change: Loaded benchmark cases from JSON, added live assistant answer metric persistence, and added generated-answer benchmark scoring.
  Purpose: Support richer datasets, track generated-answer quality over time, and regression-test answer behavior.

- `backend/app/services/ai.py`
  Change: Improved the deterministic local assistant with sentence scoring, citation deduplication, and weak-evidence refusal.
  Purpose: Produce more relevant local answers while preserving grounded no-answer behavior.

- `backend/app/api/evaluation.py`, `backend/app/models/schemas.py`
  Change: Added `task_type` selection for retrieval, answer, and combined evaluation runs.
  Purpose: Let the same evaluation endpoint run both retrieval and generated-answer benchmarks.

- `backend/app/services/ai.py`
  Change: Persisted answer quality metrics after assistant answer generation.
  Purpose: Record citation validity, unsupported term rate, and hallucination risk for live answers.

- `backend/tests/test_evaluation.py`
  Change: Added coverage for file-backed benchmarks, assistant answer metrics, answer benchmark runs, and negative-answer scoring.
  Purpose: Keep the evaluation workflow regression-tested.

- `docs/REMAINING_WORK.md`, `data/samples/README.md`
  Change: Updated AI/evaluation status and sample-data notes.
  Purpose: Keep planning docs aligned with the implementation.

### Verification

- Ran `python -m pytest -q`: 18 tests passed.
- Ran `scripts/seed_synthetic_production.py` against a temporary SQLite database.
- Ran `scripts/run_synthetic_evaluation.py` against a temporary SQLite database.

## 2026-06-18 - Workspace Hardening Pass

Area: Backend and Frontend

Goal: Implement the highest-priority follow-up work for matter/custodian management, upload workflow, document source review, Qdrant querying, auth scaffolding, and audit logging.

### Files Changed

- `backend/app/api/matters.py`
  Change: Added matter list, create, detail, and update endpoints.
  Purpose: Let the frontend manage investigation matters through real APIs.

- `backend/app/api/custodians.py`
  Change: Added custodian list, create, detail, and update endpoints.
  Purpose: Support document assignment to custodians during upload.

- `backend/app/api/audit.py`, `backend/app/models/audit_log.py`, `backend/app/services/audit.py`
  Change: Added persistent audit logging and an audit query endpoint.
  Purpose: Track matter changes, document actions, search, AI answers, and evaluation activity.

- `backend/app/core/auth.py`, `backend/app/core/config.py`
  Change: Added optional API-key authentication and matter-access guard hooks.
  Purpose: Provide a local-dev-friendly auth scaffold that can be hardened later.

- `backend/app/services/vector_store.py`, `backend/app/services/search.py`
  Change: Added Qdrant query support with local database fallback.
  Purpose: Move Qdrant beyond indexing-only behavior.

- `backend/app/api/documents.py`, `backend/app/api/search.py`, `backend/app/api/ai.py`, `backend/app/api/analytics.py`, `backend/app/api/entities.py`, `backend/app/api/graph.py`, `backend/app/api/evaluation.py`
  Change: Added matter guards, audit events, document chunks in detail responses, and search source reporting.
  Purpose: Make core workflows scoped, traceable, and citation-review ready.

- `backend/alembic/versions/0005_audit_logs.py`
  Change: Added the audit log migration.
  Purpose: Version the new audit table.

- `frontend/lib/api.ts`, `frontend/app/page.tsx`, `frontend/app/documents/[documentId]/page.tsx`
  Change: Added frontend matter/custodian management, upload, search, recent documents, and document source review with chunks, entities, and relationships.
  Purpose: Replace placeholder workspace controls with usable product workflows.

- `frontend/components/InvestigationAssistantView.tsx`, `frontend/components/AnalyticsDashboardView.tsx`, `frontend/components/KnowledgeGraphView.tsx`
  Change: Added matter selection to assistant, dashboard, and graph flows, and linked assistant sources back to document chunks.
  Purpose: Keep analysis scoped to the active matter and make AI citations reviewable.

- `docs/REMAINING_WORK.md`, `backend/README.md`
  Change: Updated project status and endpoint documentation.
  Purpose: Keep follow-up planning aligned with the new implementation.

### Verification

- Ran `python -m pytest -q`: 15 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.
- Frontend build is still pending local Node package tooling.

## 2026-06-15 - Phase 7 AI Integration

Area: Backend and Frontend

Goal: Add the first AI assistant workflow with cited answers, provider configuration, source snippets, and grounding checks.

### Files Changed

- `backend/app/core/config.py`
  Change: Added AI provider, model, and external-call enablement settings.
  Purpose: Configure AI behavior without hardcoding provider choices.

- `.env.example`
  Change: Added AI provider environment variables.
  Purpose: Document root-level AI configuration.

- `backend/.env.example`
  Change: Added AI provider environment variables.
  Purpose: Document backend AI configuration.

- `backend/app/models/schemas.py`
  Change: Added AI source, answer request, and answer response schemas.
  Purpose: Provide typed contracts for the assistant API.

- `backend/app/services/ai.py`
  Change: Added provider abstraction, local grounded provider, optional OpenAI provider, prompt construction, citation enforcement, and grounding evaluation.
  Purpose: Implement the Phase 7 assistant layer while isolating provider-specific code.

- `backend/app/api/ai.py`
  Change: Added `POST /api/ai/answer`.
  Purpose: Expose cited AI answers through FastAPI.

- `backend/app/main.py`
  Change: Registered the AI router.
  Purpose: Make assistant endpoints available under `/api/ai`.

- `backend/app/services/evaluation.py`
  Change: Ignored bracketed citations during answer term extraction.
  Purpose: Avoid treating citation syntax as unsupported answer claims.

- `backend/tests/test_ai.py`
  Change: Added tests for cited local answers, no-source behavior, and prompt construction.
  Purpose: Verify the assistant workflow without external AI calls.

- `frontend/lib/api.ts`
  Change: Added AI answer types and `askAssistant`.
  Purpose: Give the frontend typed access to `/api/ai/answer`.

- `frontend/components/InvestigationAssistantView.tsx`
  Change: Added the assistant UI.
  Purpose: Let users ask questions and inspect cited answers, sources, and grounding metrics.

- `frontend/app/assistant/page.tsx`
  Change: Added the `/assistant` route.
  Purpose: Make the assistant available in the Next.js app.

- `frontend/app/page.tsx`
  Change: Added an Assistant navigation link.
  Purpose: Make Phase 7 discoverable from the workspace entry page.

- `backend/README.md`
  Change: Documented the AI Assistant API and provider configuration.
  Purpose: Help developers run and configure Phase 7.

- `frontend/README.md`
  Change: Documented the assistant page.
  Purpose: Help developers find the Phase 7 frontend view.

- `docs/PHASE_7_CHANGES.md`
  Change: Added Phase 6 audit, Phase 7 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide the requested markdown record of Phase 7 changes.

### Verification

- Ran `python -m pytest -q`: 13 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.
- Ran `npm run build`.

### Follow-Up Notes

- External OpenAI calls are disabled by default. The local extractive provider supports safe development and testing.
- A later pass can add streaming responses, audit logs, and provider-enabled evaluation runs.

## 2026-06-15 - Phase 6 AI Evaluation Framework

Area: Backend and Evaluation

Goal: Add benchmark datasets, retrieval precision/recall metrics, citation quality checks, hallucination-risk tracking, and automated regression tests.

### Files Changed

- `backend/app/models/evaluation.py`
  Change: Added the `EvaluationRun` model.
  Purpose: Persist benchmark metric rows with dataset, case, metric, value, details, and timestamp.

- `backend/app/models/__init__.py`
  Change: Exported `EvaluationRun`.
  Purpose: Keep model imports consistent for startup, migrations, and tests.

- `backend/app/database.py`
  Change: Included the evaluation model in local database initialization.
  Purpose: Ensure the evaluation table is created during lightweight local development.

- `backend/alembic/versions/0004_evaluation_runs.py`
  Change: Added migration for `evaluation_runs`.
  Purpose: Version the Phase 6 schema.

- `backend/app/models/schemas.py`
  Change: Added benchmark, evaluation run, persisted metric, and answer-grounding schemas.
  Purpose: Provide typed API contracts for Phase 6.

- `backend/app/services/evaluation.py`
  Change: Added synthetic benchmarks, retrieval evaluation, citation validation, metric persistence, and answer grounding checks.
  Purpose: Implement deterministic AI evaluation and regression behavior.

- `backend/app/api/evaluation.py`
  Change: Added benchmark, run, metric history, and answer-check endpoints.
  Purpose: Expose the evaluation framework through FastAPI.

- `backend/tests/test_evaluation.py`
  Change: Added tests for benchmark discovery, evaluation runs, persisted metrics, citation validity, and unsupported answer terms.
  Purpose: Verify Phase 6 behavior through public API endpoints.

- `data/samples/evaluation_benchmarks.json`
  Change: Added synthetic retrieval and citation benchmark cases.
  Purpose: Provide a readable benchmark fixture for regression testing.

- `data/samples/README.md`
  Change: Documented the benchmark fixture.
  Purpose: Keep sample-data guidance clear.

- `backend/README.md`
  Change: Documented evaluation API endpoints.
  Purpose: Help developers exercise the Phase 6 backend.

- `docs/DATA_MODEL.md`
  Change: Expanded evaluation run fields.
  Purpose: Keep the planning data model aligned with the implemented schema.

- `docs/PHASE_6_CHANGES.md`
  Change: Added Phase 5 audit, Phase 6 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide the requested markdown record of Phase 6 changes.

### Verification

- Ran `python -m pytest -q`: 10 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.

### Follow-Up Notes

- The first evaluator is deterministic and local. Future work can add model-assisted judging once provider and data-handling choices are finalized.
- Additional benchmark cases should be added as synthetic productions mature.

## 2026-06-11 - Phase 5 Analytics Dashboard

Area: Backend and Frontend

Goal: Replace analytics placeholders with real dashboard data, Plotly charts, timeline analytics, and communication analysis.

### Files Changed

- `backend/app/models/schemas.py`
  Change: Added analytics bucket, timeline point, communication metric, and dashboard response schemas.
  Purpose: Provide typed contracts for Phase 5 analytics data.

- `backend/app/services/analytics.py`
  Change: Added analytics aggregation service.
  Purpose: Compute dashboard metrics from persisted documents, entities, custodians, and relationships.

- `backend/app/api/analytics.py`
  Change: Replaced placeholder snapshot values and added `/api/analytics/dashboard`.
  Purpose: Expose real analytics data to the frontend.

- `backend/tests/test_analytics.py`
  Change: Added tests for analytics snapshot and dashboard responses.
  Purpose: Verify counts, distributions, timelines, custodians, and communication pairs.

- `frontend/lib/api.ts`
  Change: Added analytics types and `getAnalyticsDashboard`.
  Purpose: Give the frontend typed access to dashboard data.

- `frontend/types/react-plotly.js.d.ts`
  Change: Added a minimal module declaration for `react-plotly.js`.
  Purpose: Allow TypeScript to compile Plotly dashboard components.

- `frontend/components/AnalyticsDashboardView.tsx`
  Change: Added the Plotly analytics dashboard UI.
  Purpose: Visualize document timelines, distributions, custodians, and communication pairs.

- `frontend/app/dashboard/page.tsx`
  Change: Replaced the placeholder dashboard with the analytics dashboard component.
  Purpose: Make `/dashboard` a working Phase 5 surface.

- `frontend/app/page.tsx`
  Change: Added a dashboard link to the workspace header.
  Purpose: Make analytics discoverable from the first screen.

- `backend/README.md`
  Change: Documented analytics API endpoints.
  Purpose: Help developers exercise the Phase 5 backend.

- `frontend/README.md`
  Change: Documented the dashboard page.
  Purpose: Help developers find the Phase 5 frontend view.

- `docs/PHASE_5_CHANGES.md`
  Change: Added Phase 4 audit, Phase 5 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide a dedicated record of the Phase 5 work.

### Verification

- Ran `python -m pytest -q`: 8 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.
- Ran `npm run build`.
- Ran a browser smoke test against `/dashboard` with temporary sample data: dashboard rendered metrics, Plotly chart content, and communication rows.

### Follow-Up Notes

- Analytics are dynamically computed from relational tables. Cached aggregate tables can be added later if dashboard latency becomes an issue.
- Phase 6 can use these metrics as part of regression fixtures.

## 2026-06-11 - Phase 4 Knowledge Graph Foundation

Area: Backend and Frontend

Goal: Add graph construction, graph queries, and relationship visualization on top of Phase 3 entity and relationship data.

### Files Changed

- `backend/app/models/schemas.py`
  Change: Added graph node, edge, metrics, graph response, and path response schemas.
  Purpose: Provide typed API contracts for graph visualization and graph queries.

- `backend/app/services/knowledge_graph.py`
  Change: Added NetworkX-backed graph construction, edge aggregation, metrics, neighborhood queries, and shortest-path queries.
  Purpose: Build knowledge graphs from persisted entities and relationships.

- `backend/app/api/graph.py`
  Change: Added graph, neighborhood, path, and metrics endpoints.
  Purpose: Expose Phase 4 graph capabilities through FastAPI.

- `backend/app/main.py`
  Change: Registered the graph router and added local-development CORS middleware.
  Purpose: Make graph APIs available to the browser frontend.

- `backend/tests/test_graph.py`
  Change: Added graph endpoint tests.
  Purpose: Verify visualization data, metrics, neighborhoods, shortest paths, and validation.

- `frontend/lib/api.ts`
  Change: Added graph types and `getKnowledgeGraph`.
  Purpose: Give the frontend typed access to `/api/graph`.

- `frontend/components/KnowledgeGraphView.tsx`
  Change: Added SVG graph visualization with metrics, selection, top entities, refresh, and relationship filtering.
  Purpose: Deliver the Phase 4 relationship visualization experience.

- `frontend/app/graph/page.tsx`
  Change: Added the `/graph` route.
  Purpose: Make the knowledge graph view available in the Next.js app.

- `frontend/app/page.tsx`
  Change: Added a graph link from the workspace header.
  Purpose: Make Phase 4 discoverable from the first screen.

- `backend/README.md`
  Change: Documented graph API endpoints.
  Purpose: Help developers exercise the Phase 4 backend.

- `frontend/README.md`
  Change: Documented the graph page.
  Purpose: Help developers find the Phase 4 frontend view.

- `docs/PHASE_4_CHANGES.md`
  Change: Added the Phase 4 audit, implementation summary, file list, verification, and follow-up notes.
  Purpose: Provide a dedicated record of the Phase 4 work.

### Verification

- Ran `python -m pytest -q`: 6 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.
- Ran `npm run build`.
- Ran a browser smoke test against `/graph` with temporary sample data: graph rendered with nodes, edges, metrics, selected entity details, and top entities.

### Follow-Up Notes

- The graph is built dynamically from relational data. A cached graph projection can be added later if graph size or latency requires it.
- Phase 5 can reuse graph metrics for dashboard widgets.

## 2026-06-11 - Backend Phase 3 Entity Extraction Foundation

Area: Backend

Goal: Verify Phase 2 and add persistent entity extraction, cited mentions, and first-pass relationship extraction.

### Files Changed

- `backend/app/models/entity.py`
  Change: Added the `Entity` model.
  Purpose: Persist normalized named entities by matter and type.

- `backend/app/models/entity_mention.py`
  Change: Added the `EntityMention` model.
  Purpose: Store cited entity mentions with document, chunk, and offset context.

- `backend/app/models/relationship.py`
  Change: Added the `Relationship` model.
  Purpose: Persist evidence-backed links between entities.

- `backend/app/models/document.py`
  Change: Added cascading relationships for entity mentions and document-scoped relationships.
  Purpose: Keep derived Phase 3 data aligned with document deletion.

- `backend/app/models/__init__.py`
  Change: Exported Phase 3 models.
  Purpose: Keep model imports consistent for startup, migrations, and tests.

- `backend/app/database.py`
  Change: Included Phase 3 models during local database initialization.
  Purpose: Ensure lightweight local development creates the new tables.

- `backend/app/models/schemas.py`
  Change: Added entity detail, mention, and relationship response schemas.
  Purpose: Return structured Phase 3 data from the API.

- `backend/app/services/entity_extraction.py`
  Change: Added rule-based NER, entity upsert, mention persistence, and relationship extraction.
  Purpose: Implement Phase 3 without requiring an external NLP service.

- `backend/app/services/ingestion.py`
  Change: Triggered entity processing after chunk creation.
  Purpose: Make uploaded documents immediately available for entity review.

- `backend/app/api/entities.py`
  Change: Replaced the placeholder route with entity list, detail, and relationship endpoints.
  Purpose: Expose persisted entities and relationships through `/api/entities`.

- `backend/alembic/versions/0003_entities_relationships.py`
  Change: Added migration for entities, entity mentions, and relationships.
  Purpose: Version the Phase 3 schema.

- `backend/tests/test_documents.py`
  Change: Added assertions for entity extraction, citations, and relationships.
  Purpose: Verify Phase 3 behavior through upload ingestion.

- `backend/README.md`
  Change: Documented entity API endpoints and extraction behavior.
  Purpose: Help developers exercise Phase 3 locally.

- `docs/DATA_MODEL.md`
  Change: Added entity mention fields and expanded entity and relationship fields.
  Purpose: Keep project docs aligned with the implementation.

- `docs/PHASE_3_CHANGES.md`
  Change: Added the Phase 2 audit, Phase 3 implementation summary, changed files, verification plan, and follow-up notes.
  Purpose: Provide the requested markdown record of Phase 3 changes.

### Verification

- Ran `python -m pytest -q`: 4 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.

### Follow-Up Notes

- The initial extractor is deterministic and rule-based. Future work can add spaCy, transformer NER, or provider-backed extraction.
- Relationship extraction currently covers co-mentions and email header communication.

## 2026-06-10 - Backend Phase 2 RAG Search Foundation

Area: Backend

Goal: Complete the Phase 1 parsing gaps and begin Phase 2 with chunked, citation-bearing search.

### Files Changed

- `backend/app/core/config.py`
  Change: Added Qdrant collection, Qdrant enablement, and embedding dimension settings.
  Purpose: Configure vector indexing while keeping local tests independent from external services.

- `backend/app/models/chunk.py`
  Change: Added the `DocumentChunk` model.
  Purpose: Persist searchable text chunks with offsets, hashes, embeddings, and vector ids.

- `backend/app/models/document.py`
  Change: Added a document-to-chunks relationship.
  Purpose: Tie chunk lifecycle to source document lifecycle.

- `backend/app/models/__init__.py`
  Change: Exported `DocumentChunk`.
  Purpose: Keep model imports consistent across startup, migrations, and tests.

- `backend/app/database.py`
  Change: Included chunk model loading in local database initialization.
  Purpose: Ensure the new table is created during lightweight local development.

- `backend/app/models/schemas.py`
  Change: Added chunk schema and expanded search result fields.
  Purpose: Return chunk ids, document ids, snippets, scores, and citations from search.

- `backend/app/services/text_extraction.py`
  Change: Added extraction for text, PDF, DOCX, and EML files.
  Purpose: Close the Phase 1 parsing gap required before useful RAG search.

- `backend/app/services/chunking.py`
  Change: Added overlapping text chunk generation.
  Purpose: Create citation-sized retrieval units from extracted document text.

- `backend/app/services/embeddings.py`
  Change: Added deterministic local embeddings and cosine similarity.
  Purpose: Enable repeatable vector-style retrieval without API keys.

- `backend/app/services/vector_store.py`
  Change: Added optional Qdrant collection setup and point indexing.
  Purpose: Prepare document chunks for Qdrant-backed retrieval when enabled.

- `backend/app/services/ingestion.py`
  Change: Wired extraction, metadata mapping, chunking, embeddings, and optional Qdrant indexing into upload ingestion.
  Purpose: Make uploaded documents immediately searchable.

- `backend/app/services/search.py`
  Change: Added database-backed chunk retrieval and ranking.
  Purpose: Replace placeholder search behavior with citation-bearing results.

- `backend/app/api/search.py`
  Change: Replaced stubbed search response with the retrieval service.
  Purpose: Expose the Phase 2 RAG foundation through `/api/search`.

- `backend/alembic/versions/0002_document_chunks.py`
  Change: Added migration for `document_chunks`.
  Purpose: Version the Phase 2 schema change.

- `backend/tests/test_documents.py`
  Change: Added assertions for parsing, metadata, and citation search.
  Purpose: Verify Phase 1 readiness and Phase 2 retrieval behavior.

- `.env.example`
  Change: Added Qdrant and embedding settings.
  Purpose: Document root environment configuration for Phase 2.

- `backend/.env.example`
  Change: Added Qdrant and embedding settings.
  Purpose: Document backend environment configuration for Phase 2.

- `backend/README.md`
  Change: Documented parsing and search behavior.
  Purpose: Help developers exercise the new workflow locally.

- `docs/DATA_MODEL.md`
  Change: Expanded the chunk model fields.
  Purpose: Keep the planning docs aligned with the implemented schema.

- `docs/PHASE_2_CHANGES.md`
  Change: Added Phase 1 audit, Phase 2 implementation summary, changed files, verification plan, and follow-up notes.
  Purpose: Provide the requested markdown record of changes and their purpose.

### Verification

- Ran `python -m pytest -q`: 4 tests passed.
- Ran `python -m compileall -q app`.
- Ran `python -m alembic upgrade head` against a temporary SQLite database.

### Follow-Up Notes

- Direct Qdrant querying can be added after the vector service is part of the expected local runtime.
- The deterministic embedding provider should be replaced or made configurable when production model-provider decisions are finalized.

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

## 2026-07-06 - Dashboard Workspace Redesign

- Rebuilt the home screen around a persistent LegalSight navigation sidebar with direct access to the AI assistant, analytics, knowledge graph, audit trail, evaluation, and administration.
- Replaced the oversized hero with a compact application top bar, active-matter switcher, notification control, and user identity.
- Added a dashboard overview with matter metrics, a responsive evidence-processing activity chart, and an `Ask LegalSight` action.
- Preserved the existing matter setup, custodian, upload, evidence search, saved search, and recent-document workflows beneath the new overview.
- Added responsive tablet and mobile navigation treatments and stronger, restrained card shadows.
- Expanded UI smoke coverage for the dashboard shell, sidebar, chart, and primary LegalSight navigation.
