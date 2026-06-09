from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def sanitize_filename(filename: str | None) -> str:
    raw_name = Path(filename or "untitled").name.strip()
    safe_name = "".join(char if char.isalnum() or char in {".", "-", "_"} else "_" for char in raw_name)
    return safe_name or "untitled"


def file_extension(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower().lstrip(".")
    return suffix or "unknown"


async def save_upload_file(file: UploadFile, upload_dir: Path) -> tuple[Path, int]:
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(file.filename)
    stored_path = upload_dir / f"{uuid4().hex}_{safe_name}"

    size_bytes = 0
    with stored_path.open("wb") as destination:
        while chunk := await file.read(1024 * 1024):
            size_bytes += len(chunk)
            destination.write(chunk)

    return stored_path, size_bytes
