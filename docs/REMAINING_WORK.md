# Remaining Work

Date: 2026-06-18

## Current Status

The project is a Phase 7 prototype of an AI-powered litigation and eDiscovery analytics platform. It already includes document ingestion, parsing, chunking, citation search, entity extraction, relationship persistence, knowledge graph views, analytics dashboards, deterministic evaluation, and a first AI assistant workflow.

The codebase is ahead of some planning docs. In particular, `docs/PHASE_7_PLAN.md` says Phase 7 has not started, while `docs/PHASE_7_CHANGES.md` and the implementation show Phase 7 is already present.

## Highest Priority Work

1. Wire up matter and custodian management. Status: first pass implemented.
   - Backend CRUD endpoints now exist for matters and custodians.
   - The frontend "Matter Setup" fields now create and select matters.
   - Matter selection is available across upload, search, assistant, dashboard, and graph flows.
   - Remaining work: add delete/archive behavior, richer validation, and user-specific matter permissions.

2. Add a real frontend upload workflow. Status: first pass implemented.
   - The placeholder Upload button has been replaced with a working upload form.
   - Uploads support optional matter and custodian assignment.
   - The workspace shows upload status and recent documents.
   - Remaining work: add progress indicators for large uploads and richer parsing error details.

3. Add document detail and source review screens. Status: first pass implemented.
   - Document detail pages show metadata, extracted text, chunks, entity mentions, and relationships.
   - Search results and assistant source citations link to document detail pages with selected chunks.
   - Remaining work: add better long-document navigation and richer source highlighting.

4. Finish Qdrant query integration. Status: first pass implemented.
   - Search now tries Qdrant first when `QDRANT_ENABLED=true`.
   - Database-backed search remains the fallback path.
   - Remaining work: add Docker-backed Qdrant tests and compare ranking quality against local retrieval.

5. Add authentication and authorization. Status: scaffold implemented.
   - Optional API-key authentication can be enabled with `AUTH_ENABLED=true` and `API_KEYS`.
   - Matter access checks are now threaded through core routes, including graph neighborhood/path requests.
   - Remaining work: replace the API-key scaffold with real users/roles and enforce user-to-matter permissions.

6. Add audit logging. Status: first pass implemented.
   - Audit events are recorded for matter/custodian changes, document upload/view/delete, search, AI answers, and evaluation checks.
   - The audit API supports filtering by matter, document, and action.
   - Remaining work: expand audit coverage and add retention/export policies.

## AI And Evaluation Work

1. Expand benchmark datasets.
   - Status: first pass implemented.
   - Benchmark cases now load from `data/samples/evaluation_benchmarks.json`.
   - Added a richer synthetic mixed-production dataset covering contracts, emails, invoices, discovery responses, legal analysis, answer cases, and negative cases.
   - Added `scripts/seed_synthetic_production.py` to load the synthetic production through the ingestion pipeline.
   - Remaining work: grow the corpus with pleadings, orders, chat exports, and more distractor documents.

2. Add generated-answer evaluation.
   - Status: first pass implemented.
   - Assistant answers now persist answer quality metrics for citation validity, unsupported term rate, and hallucination risk.
   - `/api/evaluation/run` can run answer benchmarks with `task_type: "answer"` or combined retrieval and answer benchmarks with `task_type: "all"`.
   - Negative cases are scored for proper no-answer behavior.
   - Remaining work: add provider-enabled manual evaluation and richer answer pass/fail thresholds.

3. Improve the local assistant response quality.
   - Status: first pass implemented.
   - The current local provider is extractive and deterministic.
   - It now scores evidence sentences against question terms, deduplicates citations, and refuses weak/off-topic retrievals.
   - Remaining work: improve multi-source synthesis and tune thresholds against larger benchmark sets.

4. Add optional streaming.
   - Support streaming responses for external model providers.
   - Preserve citation and grounding checks after completion.

5. Add one-command synthetic evaluation.
   - Status: implemented.
   - `scripts/run_synthetic_evaluation.py` seeds the synthetic production and runs retrieval plus answer benchmarks.

## Document Processing Work

1. Improve file parsing.
   - Status: first pass implemented.
   - PDF extraction is safer and flags blank/scanned PDFs as `needs_ocr`.
   - DOCX extraction includes paragraph and table text.
   - EML extraction records attachment names and extracts text attachments.
   - Email dates and detected text dates are normalized to UTC.
   - Remaining work: add real OCR execution, binary attachment extraction, and more native file formats.

2. Improve classification.
   - Status: first pass implemented.
   - Added richer rule-based classification for discovery responses, legal memos, invoices, court orders, pleadings, chat exports, contracts, NDAs, PDFs, and generic documents.
   - Added test coverage for legal memo classification.
   - Consider model-assisted classification after data-handling rules are finalized.

3. Improve entity extraction.
   - Status: first pass implemented.
   - Added organization suffix normalization so aliases such as `Corp.` and `Corporation` deduplicate more reliably.
   - Added person/header cleanup normalization.
   - Consider spaCy, transformer NER, or provider-backed extraction for later phases.

## Frontend Product Work

1. Replace static landing metrics with live API data.
   - Status: implemented.
   - The landing page now pulls live counts through the analytics dashboard API and refreshes them by active matter.

2. Add search UI.
   - Status: first pass implemented.
   - The workspace search panel calls `/api/search` and shows snippets, scores, citations, result source, and document links.
   - Remaining work: add advanced filters and saved searches.

3. Improve graph UX for larger graphs.
   - Status: first pass implemented.
   - Added matter, relationship type, entity type, entity search, and confidence filters.
   - Added selected-relationship review with document links.
   - Remaining work: replace the radial SVG with force-directed or clustered layout for dense graphs.

4. Add loading, empty, and error states across all pages.
   - Status: first pass implemented.
   - Workspace, assistant, graph, dashboard, and document detail pages now have clearer loading, empty, and error states.
   - Remaining work: extract shared UI state components once the design system settles.

## Security And Data Handling

1. Update `docs/SECURITY_AND_DATA_HANDLING.md`.
   - Document exactly what content is sent to external AI providers.
   - Document how to disable external calls.
   - Add guidance for privileged, confidential, and client data.

2. Keep external AI disabled by default.
   - Current behavior is correct: local mode is default, OpenAI requires explicit configuration.
   - Preserve this default for future providers.

3. Add redaction or local-model options before production use.
   - Consider PII/privilege redaction before external AI calls.
   - Consider local embeddings and local LLM options for sensitive matters.

## Database And Alembic

Alembic should stay in the project.

It is not strictly necessary for a throwaway SQLite-only prototype because the app currently calls `Base.metadata.create_all()` on startup. However, the project is designed for PostgreSQL, shared data, and production-style schema evolution. In that context, Alembic is the right tool because it provides repeatable, reviewable migrations for existing databases.

Recommended database work:

1. Keep Alembic migrations as the source of truth for shared and production-style databases.
2. Keep `create_all()` only as a lightweight local-development convenience.
3. Eventually gate startup table creation to development only, or remove it once migrations are part of normal setup.
4. Tidy `backend/alembic/env.py` to explicitly import all model modules for clarity.
5. Add a standard migration check to CI.

## Documentation Cleanup

1. Update `README.md`.
   - It still describes the first milestone more than the current Phase 7 state.

2. Update `docs/NEXT_STEPS.md`.
   - It reflects early Phase 1 work and should be replaced with current priorities.

3. Update `docs/PHASE_7_PLAN.md`.
   - Mark implemented items as complete.
   - Move remaining items into a follow-up Phase 8 or hardening plan.

4. Keep `docs/PHASE_7_CHANGES.md` as the current implementation record.

## Verification And Tooling

The local source tree does not currently include a backend virtual environment or frontend `node_modules`. Before trusting the checkout, install dependencies and run:

```powershell
cd backend
pip install -r requirements.txt
python -m pytest -q
python -m compileall -q app
alembic upgrade head

cd ../frontend
npm install
npm run build
```

Recommended follow-up tooling:

1. Add CI for backend tests, Python compile checks, Alembic migration checks, and frontend builds.
2. Add a Docker-based smoke test for Postgres and Qdrant.
3. Add a small seeded demo dataset so the UI can be reviewed consistently.

## Completed Build Order

The previous high-priority build order has been completed at first-pass/prototype level:

1. Updated stale docs so the repo accurately reflects Phase 7.
2. Added matter and custodian API endpoints.
3. Wired frontend matter setup to real APIs.
4. Added frontend upload workflow.
5. Added document detail and citation target views.
6. Added search UI.
7. Added Qdrant query support with local fallback.
8. Added API-key auth scaffold and matter-level access guard hooks.
9. Added audit logging for search and AI answers.
10. Expanded evaluation datasets and generated-answer checks.

## Suggested Next Build Order

1. Add real users, roles, and user-to-matter permission mapping.
2. Add audit retention/export policy and broader audit review UI.
3. Add Docker-backed Qdrant integration tests.
4. Add saved searches and advanced search filters.
5. Add a frontend evaluation dashboard for benchmark and answer-quality history.
6. Replace the simple graph layout with a force-directed or clustered layout.
7. Add true OCR execution and binary attachment extraction.
