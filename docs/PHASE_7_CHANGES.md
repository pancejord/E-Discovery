# Phase 7 Changes - AI Integration

Date: 2026-06-15

## Purpose

Phase 7 adds the first AI assistant workflow to the eDiscovery platform. The goal is to let users ask questions against uploaded discovery materials and receive source-grounded, cited answers with retrieval evidence and hallucination-risk signals.

The implementation keeps external AI calls disabled by default. Local extractive answer generation works without API keys, while OpenAI provider support is available behind explicit configuration.

## Phase 6 Readiness Check

Phase 6 was verified before Phase 7 work began:

- Evaluation metrics are persisted in `evaluation_runs`.
- Retrieval precision, recall, citation coverage, and benchmark pass metrics exist.
- Answer grounding checks can compare answer terms against cited chunk evidence.
- Synthetic benchmark cases exist for regression tests.

Verification before Phase 7:

- `python -m pytest -q`: 10 tests passed.
- `python -m compileall -q app`: passed.
- `python -m alembic upgrade head`: passed through `0004_evaluation_runs`.

## Phase 7 Implementation

The following capabilities were added:

- AI provider configuration for local mode and optional external provider mode.
- AI answer request and response schemas.
- Source snippet schema for cited answer evidence.
- Local extractive grounded answer provider.
- Optional OpenAI provider integration behind `AI_PROVIDER=openai`, `AI_EXTERNAL_ENABLED=true`, `AI_MODEL`, and `OPENAI_API_KEY`.
- Prompt construction that injects retrieved source excerpts and citations.
- `/api/ai/answer` endpoint.
- Automatic grounding checks on generated answers using the Phase 6 evaluator.
- Frontend `/assistant` page with question entry, cited answer display, source snippets, and grounding metrics.
- Backend tests for cited answers, no-source behavior, and prompt construction.
- Frontend API helper and navigation link for the assistant.

## Files Changed

- `backend/app/core/config.py`
  Change: Added `AI_PROVIDER`, `AI_MODEL`, and `AI_EXTERNAL_ENABLED` settings.
  Purpose: Configure AI behavior without hardcoding provider choices.

- `.env.example`
  Change: Added AI provider environment variables.
  Purpose: Document root-level AI configuration.

- `backend/.env.example`
  Change: Added AI provider environment variables.
  Purpose: Document backend AI configuration.

- `backend/app/models/schemas.py`
  Change: Added AI source, answer request, and answer response schemas.
  Purpose: Provide typed API contracts for the assistant workflow.

- `backend/app/services/ai.py`
  Change: Added provider abstraction, local grounded provider, optional OpenAI provider, prompt construction, citation enforcement, and grounding evaluation.
  Purpose: Implement the Phase 7 AI assistant layer while keeping provider code isolated.

- `backend/app/api/ai.py`
  Change: Added `POST /api/ai/answer`.
  Purpose: Expose cited AI answers through FastAPI.

- `backend/app/main.py`
  Change: Registered the AI router.
  Purpose: Make assistant endpoints available under `/api/ai`.

- `backend/app/services/evaluation.py`
  Change: Ignored bracketed citations when extracting answer terms for grounding checks.
  Purpose: Prevent citation syntax from being misclassified as unsupported answer claims.

- `backend/tests/test_ai.py`
  Change: Added tests for cited local answers, empty retrieval behavior, and prompt construction.
  Purpose: Verify the assistant workflow without external AI calls.

- `frontend/lib/api.ts`
  Change: Added AI answer types and `askAssistant`.
  Purpose: Give the frontend typed access to `/api/ai/answer`.

- `frontend/components/InvestigationAssistantView.tsx`
  Change: Added the assistant UI with question form, answer panel, source snippets, and grounding metrics.
  Purpose: Deliver the Phase 7 user-facing investigation assistant.

- `frontend/app/assistant/page.tsx`
  Change: Added the `/assistant` route.
  Purpose: Make the assistant available in the Next.js app.

- `frontend/app/page.tsx`
  Change: Added an Assistant navigation link.
  Purpose: Make Phase 7 discoverable from the workspace entry page.

- `backend/README.md`
  Change: Documented the AI Assistant API and provider configuration.
  Purpose: Help developers run and configure the Phase 7 backend.

- `frontend/README.md`
  Change: Documented the assistant page.
  Purpose: Help developers find the Phase 7 frontend view.

- `docs/CHANGE_LOG.md`
  Change: Added this Phase 7 project entry.
  Purpose: Maintain the project history in the existing change log.

- `docs/PHASE_7_CHANGES.md`
  Change: Added Phase 6 audit, Phase 7 implementation summary, changed files, verification, and follow-up notes.
  Purpose: Provide the requested markdown record of changes and their purpose.

## Verification

- `python -m pytest -q`: 13 tests passed.
- `python -m compileall -q app`: passed.
- `npm run build`: passed.
- `python -m alembic upgrade head` with `DATABASE_URL=sqlite:///./tmp_phase7_migration.db`: passed.

## Follow-Up Notes

- External OpenAI calls remain disabled by default to protect sensitive discovery data.
- The local provider is extractive and deterministic. It is intended for reliable development and graceful no-key behavior.
- The optional OpenAI provider is isolated in `backend/app/services/ai.py`, so later provider swaps can stay scoped.
- A future pass can add streaming answers, answer audit logs, and provider-enabled evaluation runs.
