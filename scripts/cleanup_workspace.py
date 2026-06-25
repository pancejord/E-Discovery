"""Remove local generated files from the workspace.

The script is intentionally scoped to known generated paths under the repository
root so it can be run after checks without touching source files or backups.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CACHE_DIRS = [
    ROOT / ".pytest_cache",
    ROOT / "backend" / ".pytest_cache",
    ROOT / "frontend" / ".next",
    ROOT / "frontend" / ".turbo",
]

DEPENDENCY_DIRS = [
    ROOT / "frontend" / "node_modules",
]

TEMP_FILES = [
    ROOT / "backend" / "_migration_check.db",
    ROOT / "frontend" / "pnpm-lock.yaml",
]

TEMP_PATTERNS = [
    "**/__pycache__",
    "tmp_*.db",
    "backend/tmp_*.db",
    "backend/*.sqlite3-journal",
    "backend/*.db-journal",
]


def assert_inside_repo(path: Path) -> Path:
    resolved = path.resolve()
    if resolved != ROOT and ROOT not in resolved.parents:
        raise ValueError(f"Refusing to clean path outside repository: {resolved}")
    return resolved


def remove_path(path: Path, dry_run: bool, removed: list[str]) -> None:
    resolved = assert_inside_repo(path)
    if not resolved.exists():
        return
    removed.append(str(resolved.relative_to(ROOT)))
    if dry_run:
        return
    if resolved.is_dir():
        shutil.rmtree(resolved)
    else:
        resolved.unlink()


def collect_pattern(pattern: str) -> list[Path]:
    return sorted(ROOT.glob(pattern), key=lambda item: str(item).lower())


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean generated workspace artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="List files and folders without removing them.")
    parser.add_argument(
        "--include-dependencies",
        action="store_true",
        help="Also remove frontend dependency folders such as frontend/node_modules.",
    )
    args = parser.parse_args()

    removed: list[str] = []

    for path in CACHE_DIRS + TEMP_FILES:
        remove_path(path, args.dry_run, removed)

    for pattern in TEMP_PATTERNS:
        for path in collect_pattern(pattern):
            remove_path(path, args.dry_run, removed)

    if args.include_dependencies:
        for path in DEPENDENCY_DIRS:
            remove_path(path, args.dry_run, removed)

    if removed:
        prefix = "Would remove" if args.dry_run else "Removed"
        print(f"{prefix} {len(removed)} generated artifact(s):")
        for item in removed:
            print(f"- {item}")
    else:
        print("No generated artifacts found.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
