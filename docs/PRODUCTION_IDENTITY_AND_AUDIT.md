# Production Identity And Audit Design

Date: 2026-06-24

## Identity Modes

### Local API-Key Mode

Use this mode for local development, demos, and prototype deployments.

- `AUTH_ENABLED=true`
- `AUTH_BEARER_ENABLED=false`
- Clients authenticate with `X-API-Key`.
- API keys are stored only as SHA-256 hashes in `users.api_key_hash`.
- Admins can create users and rotate keys from `/admin`.
- Users can be deactivated without deleting audit history.

### Bearer Token Mode

Use this mode behind a production identity gateway or as a bridge toward OIDC/SAML.

- `AUTH_ENABLED=true`
- `AUTH_BEARER_ENABLED=true`
- Clients authenticate with `Authorization: Bearer <token>`.
- The current implementation resolves the bearer token against `users.api_key_hash`, preserving the same local user, role, tenant, and matter-membership model.
- A future OIDC/SAML integration can replace token lookup with JWT validation while preserving the same `Actor` and audit context shape.

### Future OIDC/SAML Integration

Recommended production integration:

1. Validate bearer JWTs from a trusted OIDC provider.
2. Map `sub`, `email`, `name`, `groups`, `tenant`, and `organization` claims into the local `Actor`.
3. Provision or sync `users`, `roles`, and `matter_memberships` from the identity provider or an admin-managed access table.
4. Keep local API-key mode available for development and service accounts behind a separate feature flag.
5. Add session/cookie support only if the frontend moves away from direct API-token calls.

## Tenant And Organization Metadata

Users now have:

- `organization`: display-level organization or client grouping.
- `tenant_id`: stable tenant identifier for future multi-client deployment.

These fields are stored on users and copied into `details.actor_context` on audit events when the authenticated actor is known.

## Audit Request Context

Audit rows now include:

- `request_id`
- `client_ip`
- `user_agent`
- `route`
- `method`
- `response_status`

Every request also records a `request.completed` event with response status. Domain events recorded during the request, such as `matter.list` or `document.upload`, share the same request metadata and actor context.

## Audit Retention

Manual purge remains available through:

```text
POST /api/audit/retention/purge
```

Scheduled startup purge can be enabled with:

```text
AUDIT_PURGE_ON_STARTUP=true
AUDIT_RETENTION_DAYS=365
```

Startup purge records `audit.retention.purge_scheduled`. Manual purge records `audit.retention.purge_manual`.

## Audit Exports

Audit CSV and JSON exports now include `X-Audit-Export-Manifest`, a JSON header with:

- `format`
- `event_count`
- `sha256`
- `byte_count`

The export action is also recorded as `audit.export` with the same manifest in event details.
