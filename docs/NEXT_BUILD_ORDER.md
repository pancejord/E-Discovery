# Next Build Order

Date: 2026-06-19

Update 2026-06-21: Build-order steps 1 through 4 have been completed at first-pass hardening level. The frontend build is verified, persisted users/roles/matter memberships are implemented, security/data-handling docs are updated, and audit filtering/export/retention plus a review UI are in place. The next highest-priority item is Docker-backed Qdrant integration testing.

## Current Position

The project is a strong Phase 7 prototype. The core product loop now exists:
matter setup, custodian setup, upload, parsing, chunking, search, citations,
document detail views, graph/analytics pages, AI answers, evaluation checks,
Qdrant fallback support, and audit logging.

The next work should focus on hardening the platform into something closer to a
trustworthy legal product. That means proving the frontend build, enforcing real
matter-level authorization, making audit/security behavior explicit, and adding
integration coverage for the services that will matter with larger productions.

## Build Order

### 1. Verify And Fix The Frontend Build

Priority: highest

Why this comes first:

- The backend currently verifies cleanly.
- The frontend build could not be checked in the current shell because `npm` is
  unavailable.
- TypeScript or Next.js build failures can hide in otherwise working UI code.

Work:

1. Install or expose Node/npm in the local environment.
2. Run `npm install` from `frontend/`.
3. Run `npm run build`.
4. Fix any TypeScript, lint, dependency, or Next.js build issues.
5. Update docs with the verified frontend build command.

Done when:

- `npm run build` passes from `frontend/`.
- The workspace, assistant, dashboard, graph, and document detail routes build.

### 2. Add Real Users, Roles, And Matter Permissions

Priority: highest

Why this comes next:

- The current auth layer is an API-key scaffold.
- Matter access guards exist, but they do not yet check user-to-matter
  membership.
- Legal/eDiscovery workflows need strong matter isolation before realistic use.

Work:

1. Add user, role, and matter membership models.
2. Add Alembic migration for the new auth tables.
3. Replace API-key-only identity with a real actor model.
4. Enforce matter membership in document, search, AI, graph, analytics,
   evaluation, and audit routes.
5. Add tests for allowed and denied matter access.

Done when:

- A user can only access matters they are assigned to.
- Tests prove cross-matter reads and writes are rejected.
- Local development can still run with auth disabled.

### 3. Update Security And Data-Handling Documentation

Priority: high

Why this comes next:

- External AI is disabled by default, which is the right default.
- The docs still need to clearly explain what content can be sent to external
  providers and how to prevent that.
- Audit logging now exists, so the security docs should no longer describe it as
  purely future work.

Work:

1. Update `docs/SECURITY_AND_DATA_HANDLING.md`.
2. Document local AI mode versus external provider mode.
3. Document what is sent to an external model when enabled.
4. Document how to disable external AI calls.
5. Add guidance for privileged, confidential, client, and production data.
6. Document audit coverage and remaining audit gaps.

Done when:

- A developer can tell whether a workflow sends data outside the local app.
- Sensitive-data defaults are clear.
- Audit limitations are explicit.

### 4. Add Audit Retention, Export, And Review UI

Priority: high

Why this comes next:

- Audit rows are being recorded, but review and lifecycle management are thin.
- Legal workflows need defensible activity history.

Work:

1. Add audit export endpoint, likely CSV or JSON.
2. Add retention policy configuration.
3. Add filters for actor, action, matter, document, and date range.
4. Add a frontend audit review page.
5. Expand audit coverage for ingestion/indexing failures and permission denials.

Done when:

- Audit events can be searched, reviewed, and exported.
- Retention behavior is documented.
- Important failures are logged instead of silently swallowed.

### 5. Add Docker-Backed Qdrant Integration Tests

Priority: high

Why this comes next:

- Qdrant indexing and query support now exists.
- The project still needs proof that the Docker-backed vector service works
  end-to-end.

Work:

1. Add a repeatable local Qdrant test setup.
2. Seed a small set of document chunks.
3. Verify chunks are indexed into Qdrant.
4. Verify query results hydrate back into citation-bearing search results.
5. Compare local search and Qdrant result quality on benchmark cases.

Done when:

- Qdrant tests can run locally against Docker.
- Search falls back cleanly if Qdrant is unavailable.
- Ranking differences are visible in evaluation output.

### 6. Add A Frontend Evaluation Dashboard

Priority: medium-high

Why this comes next:

- The backend has deterministic retrieval and answer-quality metrics.
- The product should expose those metrics so AI quality can be reviewed over
  time.

Work:

1. Add evaluation run history UI.
2. Show benchmark pass/fail results.
3. Show answer citation validity, unsupported term rate, and hallucination risk.
4. Add controls to run retrieval, answer, or combined evaluations.
5. Link failed benchmark cases back to documents and citations when possible.

Done when:

- A reviewer can run and inspect benchmark results from the frontend.
- Failed answer or retrieval cases are visible without reading raw database rows.

### 7. Add True OCR And Attachment Extraction

Priority: medium-high

Why this comes next:

- The parser currently flags scanned PDFs as needing OCR.
- Email attachments are inventoried, but binary attachments are not deeply
  extracted.
- Real productions commonly include scanned PDFs and attachment-heavy email.

Work:

1. Add OCR execution for scanned/blank PDFs.
2. Store OCR status and warnings.
3. Extract supported binary email attachments.
4. Add tests for OCR-needed and attachment extraction flows.
5. Surface extraction failures clearly in document detail views.

Done when:

- Scanned PDFs can produce searchable text when OCR dependencies are available.
- Supported email attachments are parsed into the ingestion pipeline.
- Unsupported files produce clear warnings instead of silent gaps.

### 8. Add Saved Searches And Advanced Search Filters

Priority: medium

Why this comes next:

- Basic search works.
- Review workflows need repeatable searches and filters.

Work:

1. Add filters for custodian, date range, document type, file type, and status.
2. Add saved search persistence.
3. Add saved search frontend controls.
4. Add audit events for saved search creation and execution.

Done when:

- Users can save and rerun common searches.
- Search can be narrowed by common eDiscovery metadata.

### 9. Improve Graph Layout For Dense Matters

Priority: medium

Why this comes next:

- The graph view is usable for small matters.
- Dense productions need clustering or force-directed layout to stay readable.

Work:

1. Replace the radial SVG layout with a force-directed or clustered layout.
2. Preserve existing filters and selected-relationship review.
3. Add graph empty/loading/error states if new rendering adds async behavior.

Done when:

- Larger graphs remain navigable.
- Relationship evidence and document links remain easy to inspect.

### 10. Add CI And Repeatable Smoke Checks

Priority: medium

Why this matters:

- The backend now has enough behavior that manual checks are easy to miss.
- The frontend build needs ongoing enforcement once Node/npm is available.

Work:

1. Add backend test and compile checks.
2. Add Alembic migration check.
3. Add frontend install/build check.
4. Add optional Docker smoke checks for Postgres and Qdrant.
5. Add seeded demo-data smoke workflow.

Done when:

- A single CI run verifies backend tests, migrations, and frontend build.
- Optional service-backed checks are documented.

## Recommended Immediate Sprint

If only one sprint is planned, do these first:

1. Verify and fix the frontend build.
2. Add real users, roles, and matter permissions.
3. Update security and data-handling docs.
4. Add audit export/review basics.
5. Add Qdrant integration coverage.

This order reduces the biggest product risks first: unverified UI build,
insufficient matter isolation, unclear sensitive-data handling, incomplete audit
review, and unproven vector-service behavior.
