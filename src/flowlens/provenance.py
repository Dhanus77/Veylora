"""Lightweight run provenance for reproducible local analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path


def file_fingerprint(path: str | Path, block_size: int = 1024 * 1024) -> dict[str, str | int]:
    """Return a SHA-256 and byte count for a file without exposing its contents."""
    file_path = Path(path)
    digest = sha256()
    byte_count = 0
    with file_path.open("rb") as stream:
        while chunk := stream.read(block_size):
            digest.update(chunk)
            byte_count += len(chunk)
    stat = file_path.stat()
    return {
        "filename": file_path.name,
        "sha256": digest.hexdigest(),
        "bytes": byte_count,
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }
