"""Seed the backend with the synthetic mixed-production dataset.

Run from the repository root:

    python scripts/seed_synthetic_production.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import UploadFile

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database import SessionLocal, init_db  # noqa: E402
from app.models.custodian import Custodian  # noqa: E402
from app.models.matter import Matter  # noqa: E402
from app.services.ingestion import ingest_upload  # noqa: E402


DEFAULT_DATASET = ROOT / "data" / "samples" / "synthetic_mixed_production.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic eDiscovery benchmark data.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="Path to synthetic production JSON.")
    parser.add_argument("--matter-name", default="Synthetic Mixed Production", help="Matter name to create or reuse.")
    parser.add_argument("--matter-number", default="SYN-MIXED-001", help="Matter number to create or reuse.")
    args = parser.parse_args()

    init_db()
    payload = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    documents = payload.get("documents", [])
    if not documents:
        raise SystemExit("No documents found in dataset.")

    db = SessionLocal()
    try:
        matter = _get_or_create_matter(db, args.matter_name, args.matter_number, payload.get("description"))
        with TemporaryDirectory() as tmp_dir:
            for document in documents:
                asyncio.run(_ingest_document(db, matter, document, Path(tmp_dir)))
        print(f"Seeded {len(documents)} synthetic documents into matter {matter.id}: {matter.name}")
    finally:
        db.close()


def _get_or_create_matter(db, name: str, matter_number: str, description: str | None) -> Matter:
    matter = db.query(Matter).filter(Matter.matter_number == matter_number).one_or_none()
    if matter is not None:
        return matter
    matter = Matter(name=name, matter_number=matter_number, description=description)
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return matter


def _get_or_create_custodian(db, name: str | None) -> Custodian | None:
    if not name:
        return None
    email = f"{_slug(name)}@synthetic.local"
    custodian = db.query(Custodian).filter(Custodian.email == email).one_or_none()
    if custodian is not None:
        return custodian
    custodian = Custodian(full_name=name, email=email, organization="Synthetic Dataset")
    db.add(custodian)
    db.commit()
    db.refresh(custodian)
    return custodian


async def _ingest_document(db, matter: Matter, document: dict, tmp_dir: Path) -> None:
    filename = document["filename"]
    path = tmp_dir / filename
    path.write_text(document["text"], encoding="utf-8")
    custodian = _get_or_create_custodian(db, document.get("custodian"))
    with path.open("rb") as handle:
        upload = UploadFile(file=handle, filename=filename)
        await ingest_upload(
            db,
            upload,
            matter_id=matter.id,
            custodian_id=custodian.id if custodian else None,
        )


def _slug(value: str) -> str:
    return ".".join(part.lower() for part in value.replace("-", " ").split() if part)


if __name__ == "__main__":
    main()
