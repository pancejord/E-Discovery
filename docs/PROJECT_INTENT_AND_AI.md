# LegalSight Project Intent And AI Role

Date: 2026-06-25

## Purpose

LegalSight is intended to be an AI-assisted litigation and eDiscovery review platform. Its goal is to help legal teams turn document productions into organized, searchable, reviewable matter workspaces with defensible audit trails.

The product is not meant to replace attorney judgment. It is meant to reduce manual triage work, surface patterns earlier, preserve citations back to source material, and make review decisions easier to explain.

## Target Users

- Litigation attorneys who need cited answers, chronologies, issue analysis, and privilege-risk review.
- eDiscovery review teams who need matter-based upload, search, filtering, document coding, and saved review sets.
- Litigation support teams who need ingestion status, retry workflows, exports, audit logs, and operational controls.
- Case teams and investigators who need entity, relationship, communication, and timeline views across a production.

## Core Workflows

1. Create or select a matter.
2. Add custodians and upload documents.
3. Extract text, metadata, attachments, entities, and relationships.
4. Search by keyword, phrase, metadata, review coding, sender, recipient, date, and saved searches.
5. Review source documents with citations, chunks, tags, issue codes, privilege flags, notes, and review status.
6. Use analytics dashboards and graph views to understand activity, communications, entities, and relationships.
7. Ask AI-assisted questions and receive cited answers tied back to source documents.
8. Evaluate retrieval, answer, extraction, classification, and OCR quality over time.
9. Preserve audit logs for uploads, searches, AI usage, review actions, exports, admin changes, and access denials.

## How AI Ties Into LegalSight

AI in LegalSight is designed around evidence, citations, and governance. The system should always prefer traceable outputs over unsupported narrative.

### Retrieval And Search

LegalSight combines structured metadata, keyword search, and optional vector search. Vector search helps find conceptually related material even when the exact words differ, while keyword and metadata filters keep review sets precise and repeatable.

### Cited Assistant Answers

The assistant answers questions using retrieved document snippets and returns citations back to source documents and chunks. This makes AI output reviewable by attorneys and supports defensibility.

Current answer modes include legal-review-oriented workflows such as summaries, chronologies, issue lists, contradiction checks, privilege risk, and deposition preparation.

### Entity And Relationship Extraction

AI and NLP help identify people, organizations, dates, legal references, money amounts, locations, and communication relationships. These extracted signals support the knowledge graph, dashboards, and investigative workflows.

### Classification And Triage

Document classification and extraction signals help prioritize review, identify likely document types, surface OCR needs, and route failed processing for retry.

### Evaluation

LegalSight includes benchmark and evaluation workflows so search quality, answer quality, extraction quality, classification, and OCR-term recovery can be measured instead of guessed.

### AI Governance

LegalSight defaults to local, extractive AI behavior. External AI providers are opt-in and controlled by environment settings and per-matter policy.

Before external AI is enabled for real client data, teams should confirm:

- Client instructions and protective orders allow the workflow.
- Provider contracts and data-retention terms are approved.
- Redaction settings are appropriate.
- Prompt and source material audit requirements are satisfied.
- Attorneys understand that AI outputs are drafts requiring review.

## Current Implementation State

LegalSight currently includes first-pass versions of:

- Matter, custodian, user, role, and matter-membership management.
- API-key and bearer-token authentication modes.
- Document upload, parsing, attachment extraction, OCR signaling, and retry/reprocess endpoints.
- Search, advanced filters, saved searches, result sorting, and Qdrant-backed retrieval when enabled.
- Document detail review with coding fields and highlighted search context.
- Entity extraction, relationship extraction, graph review, analytics dashboards, and CSV exports.
- Cited AI assistant answers with grounding checks and optional external provider policy controls.
- Evaluation dashboards and benchmark tracking.
- Audit review, export manifests, retention controls, and structured request logging.
- Docker and Compose deployment assets.

## Production Readiness Priorities

LegalSight is feature-rich for a prototype, but these items should be finished before treating it as production-ready for real legal matters.

### 1. Patch Frontend Dependencies

The current frontend dependency audit reports a critical Next.js advisory and a moderate PostCSS advisory. Upgrade Next.js and related packages, then rerun:

```powershell
cd frontend
npm install
npm audit --omit=dev
npm run build
```

Do not use `npm audit fix --force` blindly in production work. Review the Next.js release notes and test the app after the upgrade.

### 2. Replace Prototype Authentication With Real Identity

The current API-key and bearer-token modes are useful for local and prototype deployments. Production should integrate with an approved identity provider through OIDC, SAML, or a gateway-validated bearer token.

Production identity should include:

- Centralized user lifecycle management.
- MFA and conditional access policies.
- Group or role synchronization.
- Tenant/client isolation.
- Clear service-account handling.

### 3. Harden Secrets And Configuration

Move secrets out of local files and into a managed secret store for deployed environments.

Recommended controls:

- Rotate API keys and provider keys.
- Separate development, staging, and production settings.
- Use least-privilege database users.
- Disable development conveniences in production.
- Verify `APP_ENVIRONMENT=production` and `DATABASE_AUTO_CREATE_TABLES=false`.

### 4. Validate External AI Policy

Before external AI is used with real productions, finish a formal policy decision for each matter.

At minimum, define:

- Whether external AI is allowed.
- Which provider and model are approved.
- What text may be sent externally.
- Whether redaction is mandatory.
- How prompts and responses are audited.
- Who can enable or change the policy.

### 5. Upgrade Production Document Processing

The current parser covers useful common formats, but real productions often require stronger native handling.

Next processing priorities:

- Production OCR toolchain with monitored workers.
- PST and MSG extraction.
- Standalone image OCR.
- Large-file upload progress and limits.
- Archive family handling with child-document lineage.
- Malware scanning and file-type validation.

### 6. Strengthen Review-Scale Operations

Larger matters will need more operational controls.

Priorities:

- Background job queue for ingestion, OCR, indexing, and extraction.
- Worker retries and dead-letter queues.
- Object storage for uploaded files.
- Database connection pooling and migration runbooks.
- Qdrant backup/restore and collection migration plans.

### 7. Expand Security Testing

Add security-focused testing before using real client data.

Important tests:

- Cross-matter access denial.
- Admin-only endpoint enforcement.
- Upload validation and malicious file rejection.
- Prompt redaction behavior.
- Audit completeness for review, export, and AI actions.
- Dependency and container vulnerability scans.

### 8. Improve Observability

Production teams will need operational visibility beyond local logs.

Add:

- Centralized structured logs.
- Error tracking.
- Metrics for ingestion throughput, queue depth, failed jobs, AI calls, and search latency.
- Alerting for failed OCR, failed vector indexing, auth failures, and storage limits.

### 9. Formalize Backup, Retention, And Legal Hold

Backups and audit retention exist at first-pass level, but production legal workflows need policy-driven controls.

Define:

- Backup frequency and restore tests.
- Matter-level retention.
- Legal hold behavior.
- Audit retention and export custody rules.
- Data deletion approval workflows.

### 10. Add Deployment Gates

Before launch, create a release checklist that blocks deployment unless core checks pass.

Suggested gates:

- Backend tests pass.
- Frontend build passes.
- Alembic drift check passes.
- Dependency audit is reviewed.
- Docker images build.
- Health checks pass.
- Smoke check passes against a staging deployment.
- AI policy and external-provider settings are verified.

## Production Decision

LegalSight is currently best described as a strong first-pass product prototype with many production-oriented foundations already present. The next work should focus less on adding new features and more on hardening security, identity, dependency health, operational reliability, document-processing scale, and AI governance.
