# Remaining Work

Date: 2026-06-23

## Current Status

The original `NEXT_BUILD_ORDER.md` work is complete at first-pass prototype level. The app now has ingestion, parsing, chunking, OCR signaling, attachment extraction, advanced filtered search, saved searches, source review pages, entity and relationship extraction, graph and analytics pages, cited AI answers, evaluation metrics, audit review/export/retention purge, optional API-key auth, matter permissions, and a first admin surface for users, roles, API-key rotation, and matter memberships.

`docs/POST_BUILD_REMAINING_WORK.md` is the active backlog. Older phase-specific change files remain historical implementation records.

## Highest Priority Remaining Items

1. Production identity hardening
   - API-key auth now works for local/prototype use.
   - Remaining work: design OIDC/SAML or bearer-token integration, add session handling, document local versus production auth modes, and add organization/tenant fields if needed.

2. Audit defensibility
   - Audit rows and exports exist, including admin-change audit events.
   - Remaining work: add request IDs, client IP, user agent, route/method, response status, scheduled retention, and immutable export manifests.

3. Document processing for real productions
   - Current processing handles common text/PDF/DOCX/EML paths, OCR signaling, optional OCR command execution, and supported text attachment extraction.
   - Remaining work: persist extracted attachments as child documents, add PST/MSG/XLSX/HTML/RTF/image/archive support, add processing-stage tracking, and expose retry/reprocess endpoints.

4. Document review coding
   - Source review and citation navigation exist.
   - Remaining work: add tags, notes, issue codes, privilege flags, review status, highlighted hits, family navigation, and bulk review actions.

5. Search and retrieval maturity
   - Advanced metadata filters and saved searches exist.
   - Remaining work: Boolean search, exact phrase search, saved search update/delete/share, richer sorting, hybrid ranking diagnostics, and Qdrant payload filtering.

6. AI governance and usefulness
   - Local cited answers, optional external provider calls, grounding checks, and evaluation metrics exist.
   - Remaining work: streaming, answer modes, clearer claim-to-citation mapping, redaction controls, per-matter AI policy, and provider-enabled evaluation scripts.

7. Evaluation expansion
   - Synthetic retrieval and answer benchmarks exist.
   - Remaining work: expand pleadings/orders/discovery responses/chat/spreadsheet fixtures, add extraction/OCR/classification benchmarks, trend charts, and triage notes.

8. Entity, graph, and analytics scale
   - Deterministic entity and relationship extraction plus graph/analytics views exist.
   - Remaining work: configurable NER providers, alias merge/split UI, richer relationship types, cached graph projections, dashboard filters, and analytics export.

9. Database and deployment hardening
   - Alembic migrations and local `create_all()` exist.
   - Remaining work: gate or remove startup `create_all()` in production, add migration drift checks, add indexes, document backup/restore, and add backend/frontend Dockerfiles with health checks.

10. Frontend structure and developer ergonomics
    - The UI is usable across workspace, assistant, dashboard, graph, audit, evaluation, document detail, and admin pages.
    - Remaining work: extract shared components, add table sorting/pagination, improve validation states, add frontend tests, and add cleanup/task scripts for generated artifacts.

## Next Recommended Sprint

1. Add request metadata and scheduled retention to audit logs.
2. Add document review coding fields and UI: tags, notes, issue codes, privilege flags, and review status.
3. Persist extracted attachments as child documents and add retry/reprocess endpoints.
4. Add production identity design notes and feature-flagged bearer-token support.

## Verification Baseline

Backend:

```powershell
cd C:\Users\jpz2294\Desktop\E-Discovery-LegalSight\backend
python -m pytest -q
python -m compileall -q app
```

Frontend:

```powershell
cd C:\Users\jpz2294\Desktop\E-Discovery-LegalSight\frontend
npm install
npm run build
```
