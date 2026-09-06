import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from rag.config import settings
from rag.models import UploadedFile


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def save_uploaded_file(source_path: str | Path) -> UploadedFile:
    source = Path(source_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")

    raw_dir = settings.RAW_DOCUMENT_DIR.resolve()
    raw_dir.mkdir(parents=True, exist_ok=True)

    document_id = uuid4()
    extension = source.suffix.lower()
    stored_path = raw_dir / f"{document_id}{extension}"

    shutil.copy2(source, stored_path)
    content_hash = _hash_file(stored_path)

    return UploadedFile(
        document_id=document_id,
        stored_path=stored_path,
        content_hash=content_hash,
        uploaded_at=datetime.now(timezone.utc),
        original_filename=source.name,
    )
