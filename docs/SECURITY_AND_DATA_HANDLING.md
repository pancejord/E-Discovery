# Security And Data Handling

## Repository Rule

Do not commit privileged, confidential, client, or production discovery data.

## Local Data

- Use `data/incoming/` for temporary local uploads.
- Use `data/processed/` for generated local artifacts.
- Use `data/samples/` only for synthetic or approved test material.

## AI Usage

- All AI workflows should preserve source citations.
- Sensitive data handling should be reviewed before sending content to external model providers.
- Keep provider keys in local `.env` files only.

## Auditability

Future versions should log ingestion events, search requests, AI responses, citation sources, and evaluation results.
