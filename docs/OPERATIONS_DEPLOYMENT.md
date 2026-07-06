# Operations And Deployment

Date: 2026-06-25

This note covers persistence hardening, environment settings, backup/restore scripts, and Docker Compose profiles.

## Database Startup

The backend no longer relies on automatic table creation for production.

- `APP_ENVIRONMENT=development` and `DATABASE_AUTO_CREATE_TABLES=true` allow local `create_all()` convenience.
- `APP_ENVIRONMENT=production` or `DATABASE_AUTO_CREATE_TABLES=false` disables startup table creation.
- Shared and production databases should run `alembic upgrade head`.
- CI and `scripts/check_migration_drift.py` run `alembic check` so model/migration drift fails fast.

## Persistence Scripts

Run from the repository root:

```powershell
python scripts/check_migration_drift.py
python scripts/backup_database.py --database-url sqlite:///./backend/dev.db
python scripts/restore_database.py backups/example.sqlite3 --database-url sqlite:///./backend/dev.db --yes
python scripts/reset_demo_database.py --seed --yes
```

PostgreSQL backups use `pg_dump`; PostgreSQL restores use `pg_restore`. Those binaries must be available on PATH.

## Docker Compose Profiles

App-only, SQLite-backed:

```powershell
docker compose --profile app up --build
```

App plus Postgres:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@postgres:5432/ediscovery"
docker compose --profile app-postgres up --build
```

App plus Postgres and Qdrant:

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@postgres:5432/ediscovery"
$env:QDRANT_ENABLED="true"
docker compose --profile full up --build
```

Data services only:

```powershell
docker compose --profile postgres --profile qdrant up -d
```

## Environment Reference

Core backend settings:

- `APP_ENVIRONMENT`: `development`, `test`, or `production`.
- `DATABASE_AUTO_CREATE_TABLES`: enable/disable local startup table creation.
- `DATABASE_URL`: SQLAlchemy database URL.
- `UPLOAD_DIR`: stored uploads directory.
- `RUN_MIGRATIONS_ON_STARTUP`: container entrypoint migration toggle.
- `LOG_LEVEL`: Python logging level.
- `STRUCTURED_LOGS`: emit compact JSON request logs when true.

Search and extraction:

- `QDRANT_URL`, `QDRANT_COLLECTION`, `QDRANT_ENABLED`
- `EMBEDDING_DIMENSION`
- `OCR_ENABLED`, `OCR_PDF_TO_TEXT_COMMAND`, `OCR_TIMEOUT_SECONDS`
- `ENTITY_EXTRACTION_PROVIDER`, `SPACY_MODEL`
- `GRAPH_CACHE_TTL_SECONDS`

AI and auth:

- `AI_PROVIDER`, `AI_MODEL`, `AI_EXTERNAL_ENABLED`, `OPENAI_API_KEY`
- `AUTH_ENABLED`, `AUTH_BEARER_ENABLED`, `API_KEYS`
- `AUDIT_RETENTION_DAYS`, `AUDIT_PURGE_ON_STARTUP`

Frontend:

- `NEXT_PUBLIC_API_BASE_URL`

## Health Checks

Compose health checks cover:

- Backend: `GET /health`
- Frontend: `GET /`
- Postgres: `pg_isready`
- Qdrant: `GET /healthz`

## Logging

Set `STRUCTURED_LOGS=true` for JSON request logs with method, path, response status, and duration. Audit events remain persisted separately in `audit_logs`.
