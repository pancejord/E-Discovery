"""Reset a local demo SQLite database and optionally seed synthetic data."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DEFAULT_DB = BACKEND / "dev.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset the local demo SQLite database.")
    parser.add_argument("--database", default=str(DEFAULT_DB))
    parser.add_argument("--seed", action="store_true", help="Seed synthetic mixed-production data after migrations.")
    parser.add_argument("--yes", action="store_true", help="Confirm database replacement.")
    args = parser.parse_args()
    if not args.yes:
        raise SystemExit("Refusing to reset without --yes.")

    database_path = Path(args.database).resolve()
    database_path.unlink(missing_ok=True)
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{database_path.as_posix()}", "DATABASE_AUTO_CREATE_TABLES": "false"}
    _run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env)
    if args.seed:
        _run([sys.executable, "scripts/seed_synthetic_production.py"], cwd=ROOT, env=env)


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
