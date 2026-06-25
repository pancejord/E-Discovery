# Roadmap

Date: 2026-06-23

## Completed Prototype Phases

### Phase 1 - Document Processing Foundation

- Matter, custodian, and document persistence
- Upload storage and document listing/detail APIs
- Alembic migration foundation

### Phase 2 - RAG Search

- Text extraction for common formats
- Chunking, deterministic embeddings, and citation-bearing search
- Optional Qdrant indexing and retrieval fallback

### Phase 3 - Entity Extraction

- Deterministic entity extraction and normalization
- Entity mentions with citations
- Relationship persistence

### Phase 4 - Knowledge Graph

- Graph construction from entities and relationships
- Graph APIs and frontend visualization
- Relationship review links back to source documents

### Phase 5 - Analytics Dashboard

- Live document, entity, relationship, file type, custodian, and timeline metrics
- Communication pair analysis
- Frontend dashboard page

### Phase 6 - AI Evaluation Framework

- Synthetic benchmark datasets
- Retrieval and answer evaluation
- Citation quality and hallucination-risk metrics

### Phase 7 - Cited AI Assistant

- Local cited answer provider
- Optional external OpenAI provider mode
- Grounding checks and source review links

### Phase 8 - Search And Processing Hardening

- Optional OCR execution hook
- Email attachment extraction
- Advanced search filters
- Saved searches

### Phase 9 - Graph And Evaluation UX

- Denser graph layout and graph filters
- Evaluation dashboard
- Qdrant comparison support

### Phase 10 - CI And Smoke Checks

- Backend tests, compile checks, migrations, frontend build checks, and optional Qdrant smoke path
- Local smoke script

### Phase 11 - Administration Foundation

- Admin APIs for roles, users, user deactivation, API-key generation/rotation, and matter memberships
- Admin frontend page
- Audit events for role, user, key, and membership changes

## Current Hardening Roadmap

1. Audit defensibility
   - Add request IDs, IP/user-agent metadata, response status, scheduled retention, and immutable export manifests.

2. Review coding
   - Add tags, notes, issue codes, privilege flags, review status, family navigation, and bulk actions.

3. Production document processing
   - Persist child attachments, add PST/MSG/XLSX/HTML/RTF/image/archive handlers, track processing stages, and add retry/reprocess endpoints.

4. Production identity
   - Design and implement feature-flagged bearer/OIDC support while preserving local API-key mode.

5. Retrieval maturity
   - Add Boolean and phrase search, saved search update/delete/share, richer sorting, and hybrid ranking diagnostics.

6. AI governance
   - Add redaction controls, per-matter AI policy, streaming external provider responses, and answer modes.

7. Operational readiness
   - Add deployment Dockerfiles, environment reference docs, health checks, migration drift checks, indexes, backup/restore docs, and cleanup/task scripts.
