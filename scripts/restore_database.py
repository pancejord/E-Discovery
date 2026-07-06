"""Restore a local database backup.

SQLite restores replace the target database file. PostgreSQL restores use
pg_restore, which must be available on PATH.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_URL = "sqlite:///./backend/dev.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore a database backup.")
    parser.add_argument("backup_path")
    parser.add_argument("--database-url", default=DEFAULT_SQLITE_URL)
    parser.add_argument("--yes", action="store_true", help="Confirm replacement of the target database.")
    args = parser.parse_args()
    if not args.yes:
        raise SystemExit("Refusing to restore without --yes.")

    backup_path = Path(args.backup_path).resolve()
    url = make_url(args.database_url)
    if url.drivername.startswith("sqlite"):
        target = Path(url.database or "")
        if not target.is_absolute():
            target = (ROOT / target).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, target)
        print(target)
        return

    completed = subprocess.run(["pg_restore", "--clean", "--if-exists", "--dbname", args.database_url, str(backup_path)], check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
