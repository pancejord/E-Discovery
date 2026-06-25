# Scripts

Utility scripts live here as the project grows.

## Available Scripts

- `seed_synthetic_production.py` - load `data/samples/synthetic_mixed_production.json` through the backend ingestion pipeline.
- `run_synthetic_evaluation.py` - seed the synthetic production and run retrieval plus answer benchmarks.
- `smoke_check.py` - run repeatable backend tests, compile checks, and Alembic migration checks, with optional frontend, synthetic evaluation, and Docker-backed Qdrant checks.
- `check_migration_drift.py` - run Alembic upgrade/check against a temporary SQLite database.
- `backup_database.py` - create a SQLite copy or PostgreSQL `pg_dump` backup.
- `restore_database.py` - restore a SQLite copy or PostgreSQL `pg_restore` backup.
- `reset_demo_database.py` - rebuild a local SQLite demo database and optionally seed synthetic data.
- `cleanup_workspace.py` - remove generated caches, build output, Python bytecode, and temporary SQLite databases.
- `tasks.ps1` - run common local workflows through short PowerShell task aliases.

Run from the repository root:

```powershell
cd C:\Users\jpz2294\Desktop\E-Discovery-LegalSight
backend\.venv\Scripts\python.exe scripts\seed_synthetic_production.py
backend\.venv\Scripts\python.exe scripts\run_synthetic_evaluation.py
backend\.venv\Scripts\python.exe scripts\smoke_check.py --frontend
backend\.venv\Scripts\python.exe scripts\check_migration_drift.py
backend\.venv\Scripts\python.exe scripts\reset_demo_database.py --seed --yes
backend\.venv\Scripts\python.exe scripts\cleanup_workspace.py --dry-run
.\scripts\tasks.ps1 frontend-ui
```

Optional service-backed checks:

```powershell
docker compose up -d qdrant
backend\.venv\Scripts\python.exe scripts\smoke_check.py --qdrant
```

Back up and restore a local SQLite database:

```powershell
backend\.venv\Scripts\python.exe scripts\backup_database.py --database-url sqlite:///./backend/dev.db
backend\.venv\Scripts\python.exe scripts\restore_database.py backups/example.sqlite3 --database-url sqlite:///./backend/dev.db --yes
```

Developer runtime notes, bundled Codex desktop command examples, Node version guidance, and task aliases are documented in `docs/DEVELOPER_ENVIRONMENT.md`.
