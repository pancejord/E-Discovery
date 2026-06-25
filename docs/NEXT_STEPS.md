# Next Steps

Date: 2026-06-23

The active backlog is `docs/POST_BUILD_REMAINING_WORK.md`. This file is the shorter working queue for the next sprint.

## Completed In The Current Sprint

1. Refreshed stale planning docs so current project status is no longer contradicted by older phase notes.
2. Updated the data model reference with users, roles, matter memberships, audit logs, saved searches, document processing metadata, and evaluation details.
3. Added admin APIs and frontend controls for users, roles, API-key rotation, user deactivation, and matter memberships.

## Recommended Next Work

1. Expand audit metadata
   - Add request ID, route, method, status code, client IP, and user agent.
   - Add scheduled retention instead of manual purge only.
   - Add immutable export manifests.

2. Add document coding
   - Add tags, notes, issue codes, privilege flags, and review status.
   - Add filters and bulk updates for coded documents.
   - Record coding changes in audit logs.

3. Persist extracted attachments as child documents
   - Convert supported extracted attachments into child `documents` rows.
   - Add document-family navigation.
   - Add retry/reprocess endpoints for failed extraction, OCR, indexing, and entity extraction.

4. Design production identity
   - Document local API-key mode versus production identity-provider mode.
   - Add feature-flagged bearer-token support.
   - Decide whether organization or tenant fields are required.

## Suggested Verification Before Starting

```powershell
cd C:\Users\jpz2294\Desktop\E-Discovery-LegalSight
python scripts/smoke_check.py
```
