# Phase 7 Plan - AI Integration

Date: 2026-06-15

## Purpose

Phase 7 should add the actual AI assistant layer on top of the existing eDiscovery platform. Earlier phases built the foundation: ingestion, parsing, chunking, search, citations, entities, graph analytics, dashboarding, and evaluation. Phase 7 should connect those capabilities to a live AI workflow that can answer legal investigation questions with source-grounded citations.

No implementation has been started for this phase.

## Current Foundation

The project already has:

- Document upload, persistence, parsing, and metadata extraction.
- Document chunking and stored chunk-level citations.
- Local deterministic embeddings for development and repeatable tests.
- Optional Qdrant indexing.
- Citation-based search through `/api/search`.
- Entity extraction and relationship persistence.
- Knowledge graph construction and graph queries.
- Analytics dashboard endpoints and frontend views.
- Evaluation framework for retrieval quality, citation quality, and hallucination-risk checks.

## Phase 7 Workstreams

### 1. LLM Answer Generation

Goal: Add a backend endpoint that can answer user questions from retrieved document evidence.

Proposed work:

- Add an endpoint such as `POST /api/ai/answer`.
- Accept a user question, optional `matter_id`, and retrieval limit.
- Retrieve relevant chunks using the existing search service.
- Build a prompt from retrieved chunks and their citations.
- Generate an answer grounded only in the supplied evidence.
- Return answer text, cited source chunks, confidence or grounding metadata, and evaluation signals.

Purpose:

- Turn the project from search plus analytics into an investigation assistant.
- Keep every answer traceable to document evidence.

### 2. AI Provider Integration

Goal: Add a provider abstraction so the app can use OpenAI, Azure OpenAI, or a local model without spreading provider-specific code through the backend.

Proposed work:

- Add AI provider settings to backend configuration.
- Read model/provider keys from `.env`.
- Create an AI client/service module.
- Support at least one initial provider.
- Keep provider calls isolated behind a small interface.
- Add safe fallback behavior when no provider key is configured.

Purpose:

- Make AI features configurable and easier to swap.
- Avoid coupling routes and business logic directly to one vendor SDK.

### 3. Grounding And Citation Enforcement

Goal: Ensure generated answers are tied to source documents and can be evaluated.

Proposed work:

- Require answers to cite retrieved chunk citations.
- Reject or flag answers that include claims without cited support.
- Run the Phase 6 answer-grounding check on generated answers.
- Return hallucination-risk and citation-validity metrics with the answer.
- Persist evaluation metrics for generated answers.

Purpose:

- Preserve the project principle that AI output must be grounded in documents, citations, metadata, and measurable quality checks.

### 4. Frontend Investigation Assistant

Goal: Add a usable AI-assisted investigation interface.

Proposed work:

- Add a frontend page or panel for asking questions.
- Show generated answers with citations.
- Show source snippets beneath each citation.
- Link citations back to document details, entities, or graph context when available.
- Include loading, empty, error, and no-provider states.

Purpose:

- Give attorneys and eDiscovery users a direct workflow for asking evidence-based questions.

### 5. Qdrant Query Integration

Goal: Move beyond optional Qdrant indexing and support vector retrieval from Qdrant when configured.

Proposed work:

- Add Qdrant query support to the search service.
- Keep local database retrieval as a fallback.
- Compare Qdrant retrieval results against existing citation search behavior.
- Add tests or manual checks for both local and Qdrant-enabled paths.

Purpose:

- Prepare search for larger document sets where database-only retrieval will not be enough.

### 6. Evaluation And Regression Expansion

Goal: Extend Phase 6 evaluation to cover live AI answer generation.

Proposed work:

- Add benchmark questions that expect generated answers.
- Measure citation validity for generated answers.
- Measure answer grounding using existing chunk evidence.
- Track hallucination-risk scores over time.
- Add automated regression tests for provider-disabled behavior.
- Add optional provider-enabled evaluation scripts for local/manual runs.

Purpose:

- Make AI quality measurable before the system is trusted for legal workflows.

### 7. Security And Data Handling Review

Goal: Ensure AI provider usage respects legal-data sensitivity.

Proposed work:

- Document what content is sent to external AI providers.
- Add configuration to disable external AI calls.
- Keep provider keys out of the repo.
- Add warnings or safeguards for production/client data.
- Consider redaction or local-model options before sensitive data is sent externally.

Purpose:

- Keep the platform aligned with eDiscovery confidentiality expectations.

### 8. Production Hardening

Goal: Prepare the AI assistant workflow for a more realistic demo or deployment.

Proposed work:

- Add authentication and matter scoping before multi-user use.
- Add matter management UI.
- Improve PDF, DOCX, EML, and native file parsing.
- Add document detail/source viewer routes.
- Add API request logging and audit trails for AI answers.
- Add CI checks for tests, migrations, and build.

Purpose:

- Move from prototype-grade AI workflows toward a production-style legal analytics platform.

## Suggested Build Order

1. Add backend AI provider configuration and service abstraction.
2. Add a provider-disabled fallback response.
3. Add `POST /api/ai/answer` using existing search chunks.
4. Enforce citations in generated answers.
5. Run Phase 6 grounding checks on generated answers.
6. Add frontend ask/search assistant UI.
7. Add Qdrant query support.
8. Expand evaluation benchmarks for generated answers.
9. Add audit logging and security documentation.

## Acceptance Criteria

Phase 7 should be considered complete when:

- A user can ask a question through an API endpoint.
- The backend retrieves relevant document chunks.
- The AI provider generates an answer using only retrieved evidence.
- The response includes citations and source snippets.
- The response includes grounding or hallucination-risk signals.
- The frontend provides a usable ask interface.
- Provider-disabled mode behaves gracefully.
- Tests cover the provider-disabled path, prompt construction, citation validation, and grounding checks.
- Documentation explains provider configuration, data handling, and limitations.

## Follow-Up Notes

- Phase 7 should not bypass the existing retrieval and evaluation layers.
- The first implementation should prioritize cited, grounded answers over conversational polish.
- External AI calls should remain configurable and disabled by default until data-handling rules are reviewed.
