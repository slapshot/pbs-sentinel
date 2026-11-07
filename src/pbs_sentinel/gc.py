"""Parse missing chunk evidence from saved PBS garbage-collection logs."""

from __future__ import annotations

from pathlib import Path
import re

from .audit import Finding

MISSING_CHUNK = re.compile(
    r'warning:\s+unable to access non-existent chunk\s+'
    r'([0-9a-fA-F]{64}),\s+required by\s+"([^"\r\n]+)"',
    flags=re.IGNORECASE,
)


def parse_gc_log(contents: str) -> list[Finding]:
    """Extract references; do not assume that the chunk is still missing."""
    result: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for match in MISSING_CHUNK.finditer(contents):
        digest, index_path = match.group(1).lower(), match.group(2)
        key = (digest, index_path)
        if key in seen:
            continue
        seen.add(key)
        result.append(Finding(
            code="missing_chunk",
            severity="warning",
            message="GC log reports a missing chunk required by an index.",
            chunk_digest=digest,
            index_path=index_path,
        ))
    return result


def read_gc_log(path: Path, *, max_bytes: int = 16_000_000) -> list[Finding]:
    """Limit input size to avoid inadvertently ingesting very large logs."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("GC log must be an existing non-symlink regular file.")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"GC log exceeds the {max_bytes}-byte size limit.")
    return parse_gc_log(path.read_text(encoding="utf-8", errors="replace"))
