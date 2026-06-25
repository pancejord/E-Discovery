"""Create a local database backup.

SQLite backups copy the database file. PostgreSQL backups use pg_dump, which
must be available on PATH.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_URL = "sqlite:///./backend/dev.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="Back up the configured application database.")
    parser.add_argument("--database-url", default=DEFAULT_SQLITE_URL)
    parser.add_argument("--output-dir", default=str(ROOT / "backups"))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    url = make_url(args.database_url)
    if url.drivername.startswith("sqlite"):
        source = Path(url.database or "")
        if not source.is_absolute():
            source = (ROOT / source).resolve()
        target = output_dir / f"ediscovery-{timestamp}.sqlite3"
        shutil.copy2(source, target)
        print(target)
        return

    target = output_dir / f"ediscovery-{timestamp}.dump"
    with target.open("wb") as handle:
        completed = subprocess.run(["pg_dump", args.database_url], stdout=handle, check=False)
    if completed.returncode != 0:
        target.unlink(missing_ok=True)
        raise SystemExit(completed.returncode)
    print(target)


if __name__ == "__main__":
    main()
