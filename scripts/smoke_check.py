"""Run repeatable local smoke checks for the eDiscovery workspace.

Examples:
    python scripts/smoke_check.py
    python scripts/smoke_check.py --frontend
    python scripts/smoke_check.py --synthetic-evaluation
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run backend, migration, frontend, and optional service smoke checks.")
    parser.add_argument("--frontend", action="store_true", help="Run frontend install and production build.")
    parser.add_argument("--synthetic-evaluation", action="store_true", help="Seed synthetic data and run benchmark checks.")
    parser.add_argument("--qdrant", action="store_true", help="Run Docker-backed Qdrant integration tests.")
    args = parser.parse_args()

    _backend_checks()
    if args.synthetic_evaluation:
        _synthetic_evaluation()
    if args.frontend:
        _frontend_checks()
    if args.qdrant:
        _qdrant_checks()


def _backend_checks() -> None:
    _run([sys.executable, "-m", "pytest", "-q"], cwd=BACKEND)
    _run([sys.executable, "-m", "compileall", "-q", "app"], cwd=BACKEND)
    migration_db = BACKEND / "tmp_smoke_migration.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{migration_db.as_posix()}"}
    try:
        _run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env)
        _run([sys.executable, "scripts/check_migration_drift.py"], cwd=ROOT, env=env)
    finally:
        migration_db.unlink(missing_ok=True)


def _synthetic_evaluation() -> None:
    smoke_db = ROOT / "tmp_smoke_synthetic.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{smoke_db.as_posix()}"}
    try:
        _run([sys.executable, "scripts/run_synthetic_evaluation.py"], cwd=ROOT, env=env)
    finally:
        smoke_db.unlink(missing_ok=True)


def _frontend_checks() -> None:
    package_manager = os.environ.get("FRONTEND_PACKAGE_MANAGER", "npm")
    if package_manager == "pnpm":
        _run(["pnpm", "install", "--ignore-scripts"], cwd=FRONTEND)
        _run(["pnpm", "build"], cwd=FRONTEND)
        return
    _run([package_manager, "ci"], cwd=FRONTEND)
    _run([package_manager, "run", "build"], cwd=FRONTEND)


def _qdrant_checks() -> None:
    env = {**os.environ, "QDRANT_ENABLED": "true"}
    _run(["docker", "compose", "up", "-d", "qdrant"], cwd=ROOT)
    try:
        _run([sys.executable, "-m", "pytest", "tests/test_qdrant_integration.py", "-q"], cwd=BACKEND, env=env)
    finally:
        _run(["docker", "compose", "stop", "qdrant"], cwd=ROOT, check=False)


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None, check: bool = True) -> None:
    print(f"\n$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    if check and completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
