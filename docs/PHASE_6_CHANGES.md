# Phase 6 Changes

Date: 2026-06-15

## Purpose

Phase 6 adds the AI evaluation framework for the litigation and eDiscovery platform. The goal is to measure whether retrieval and AI-facing answers are grounded in source documents, cited correctly, and stable enough for regression testing.

This implementation is deterministic and local. It does not call external AI providers, which keeps benchmark runs repeatable and safe for synthetic/local development data.

## Phase 5 Readiness Check

Phase 5 was verified before Phase 6 work began:

- `/api/analytics/snapshot` and `/api/analytics/dashboard` return real analytics data.
- The frontend `/dashboard` renders Plotly chart content and communication analysis.
- Analytics tests cover counts, distributions, timelines, custodians, and communication pairs.

Verification before Phase 6:

- `python -m pytest -q`: 8 tests passed.
- `python -m compileall -q app`: passed.

## Phase 6 Implementation

The following capabilities were added:

- Persistent evaluation metric rows in `evaluation_runs`.
- Alembic migration for the evaluation table.
- Synthetic benchmark cases for retrieval and citation regression.
- Retrieval precision checks.
- Retrieval recall checks.
- Citation coverage and citation validity checks.
- Benchmark pass/fail metric rows.
- Answer grounding checks that compare answer terms against cited chunk evidence.
- Hallucination-risk scoring based on unsupported terms and invalid/missing citations.
- Evaluation API endpoints for benchmarks, running evaluations, metric history, and answer checks.
- Regression tests for benchmark execution, metric persistence, citation checks, and unsupported answer terms.

## Files Changed

- `backend/app/models/evaluation.py`
  Change: Added the `EvaluationRun` SQLAlchemy model.
  Purpose: Persist benchmark metric rows with matter, dataset, case, metric, value, details, and timestamp.

- `backend/app/models/__init__.py`
  Change: Exported `EvaluationRun`.
  Purpose: Keep model imports consistent for startup, migrations, and tests.

- `backend/app/database.py`
  Change: Imported the evaluation model during local table initialization.
  Purpose: Ensure lightweight local development creates the evaluation table.

- `backend/alembic/versions/0004_evaluation_runs.py`
  Change: Added migration for `evaluation_runs`.
  Purpose: Version the Phase 6 database schema.

- `backend/app/models/schemas.py`
  Change: Added benchmark, evaluation run, evaluation metric, answer-check request, and answer-check response schemas.
  Purpose: Provide typed contracts for the Phase 6 API.

- `backend/app/services/evaluation.py`
  Change: Added benchmark definitions, retrieval evaluation, citation validation, metric persistence, and grounding checks.
  Purpose: Implement deterministic AI evaluation behavior without external model calls.

- `backend/app/api/evaluation.py`
  Change: Replaced the placeholder metrics endpoint and added benchmark, run, and answer-check endpoints.
  Purpose: Expose the evaluation framework through FastAPI.

- `backend/tests/test_evaluation.py`
  Change: Added tests for benchmark listing, evaluation runs, persisted metrics, valid citations, and unsupported answer terms.
  Purpose: Verify Phase 6 behavior through public API endpoints.

- `data/samples/evaluation_benchmarks.json`
  Change: Added synthetic benchmark dataset metadata and cases.
  Purpose: Provide a readable benchmark fixture for regression testing.

- `data/samples/README.md`
  Change: Documented the benchmark fixture file.
  Purpose: Keep sample-data guidance clear.

- `backend/README.md`
  Change: Documented evaluation API endpoints.
  Purpose: Help developers exercise the Phase 6 backend.

- `docs/DATA_MODEL.md`
  Change: Expanded the evaluation run fields.
  Purpose: Keep the planning data model aligned with the implemented schema.

- `docs/CHANGE_LOG.md`
  Change: Added this Phase 6 project entry.
  Purpose: Maintain the project history in the existing change log.

- `docs/PHASE_6_CHANGES.md`
  Change: Added Phase 5 audit, Phase 6 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide the requested markdown record of changes and their purpose.

## Verification

- `python -m pytest -q`: 10 tests passed.
- `python -m compileall -q app`: passed.
- `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///./tmp_phase6_migration.db`: passed.

## Follow-Up Notes

- The first benchmark dataset is intentionally synthetic and small. More legal-domain benchmark cases can be added as sample productions mature.
- The answer-grounding check is heuristic. A future model-assisted evaluator can be added after provider and sensitive-data policies are finalized.
- Phase 6 now gives the project regression hooks for retrieval quality, citation quality, and hallucination-risk tracking.
