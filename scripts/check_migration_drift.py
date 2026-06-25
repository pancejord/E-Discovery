"""Fail when SQLAlchemy models and Alembic migrations differ.

Run from the repository root:

    python scripts/check_migration_drift.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def main() -> None:
    drift_db = BACKEND / "tmp_migration_drift.db"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{drift_db.as_posix()}",
        "DATABASE_AUTO_CREATE_TABLES": "false",
    }
    try:
        _run([sys.executable, "-m", "alembic", "upgrade", "head"], env)
        _run([sys.executable, "-m", "alembic", "check"], env)
    finally:
        drift_db.unlink(missing_ok=True)


def _run(command: list[str], env: dict[str, str]) -> None:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=BACKEND, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
