# Security And Data Handling

## Repository Rule

Do not commit privileged, confidential, client, or production discovery data.

## Local Data

- Use `data/incoming/` for temporary local uploads.
- Use `data/processed/` for generated local artifacts.
- Use `data/samples/` only for synthetic or approved test material.

## AI Usage

- Local AI mode is the default. With `AI_PROVIDER=local` and `AI_EXTERNAL_ENABLED=false`, answer generation is extractive and runs against local retrieved snippets without sending document content to an external model provider.
- External provider mode is opt-in. To call OpenAI, set `AI_PROVIDER=openai`, `AI_EXTERNAL_ENABLED=true`, `AI_MODEL`, and `OPENAI_API_KEY`.
- When external mode is enabled, the assistant can send the user's question plus retrieved source excerpts, titles, and citations to the provider. Do not enable this for privileged, confidential, client, or production data unless the provider, agreement, client instructions, protective order, and internal policy permit it.
- Disable external AI calls by leaving `AI_EXTERNAL_ENABLED=false`, omitting provider API keys, or setting `AI_PROVIDER=local`.
- All AI workflows should preserve source citations and grounding checks.
- Keep provider keys in local `.env` files only.

## Authentication And Matter Isolation

- Local development runs with `AUTH_ENABLED=false` by default.
- With `AUTH_ENABLED=true`, `X-API-Key` values are matched to persisted users by `users.api_key_hash`.
- Non-admin users can only access matters with matching `matter_memberships` rows.
- Cross-matter reads and writes are rejected and logged as `permission.denied`.
- Document uploads require a `matter_id` when auth is enabled.

## Auditability

- Audit logging currently covers matter and custodian management, document upload/view/delete, search requests, AI answer generation, evaluation runs, answer-grounding checks, permission denials, and ingestion failures.
- Audit logs can be reviewed through `/audit`, filtered through `GET /api/audit`, and exported with `GET /api/audit/export?format=csv|json`.
- `AUDIT_RETENTION_DAYS` controls retention for `POST /api/audit/retention/purge`; the default is 365 days.
- Remaining gaps: retention purge is explicit rather than scheduled, audit rows do not yet include request IDs or client IP addresses, and lower-level vector indexing failures are not surfaced with full retry context.

## Sensitive Data Guidance

- Do not commit privileged, confidential, client, or production discovery data.
- Use synthetic or approved test material in `data/samples/`.
- Treat client productions, privileged documents, legal work product, personal data, and confidential business records as local-only unless a specific external-processing review approves otherwise.
