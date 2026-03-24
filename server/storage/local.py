"""Local filesystem storage backend implementation."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote


class LocalStorageBackend:
    """Store objects under a root directory using key-like relative paths."""

    def __init__(self, *, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def put_object(self, *, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        _ = content_type
        path = self._key_to_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get_object(self, *, key: str) -> bytes:
        path = self._key_to_path(key)
        return path.read_bytes()

    def list_objects(self, *, prefix: str = "") -> list[str]:
        normalized_prefix = _normalize_key(prefix)
        results: list[str] = []
        for path in sorted(self._root.rglob("*")):
            if not path.is_file():
                continue
            relative_key = path.relative_to(self._root).as_posix()
            if normalized_prefix and not relative_key.startswith(normalized_prefix):
                continue
            results.append(relative_key)
        return results

    def delete_object(self, *, key: str) -> None:
        path = self._key_to_path(key)
        if path.exists():
            path.unlink()

    def generate_presigned_url(self, *, key: str, expires_in_seconds: int) -> str:
        path = self._key_to_path(key)
        return f"file://{quote(str(path))}?expires_in={expires_in_seconds}"

    def _key_to_path(self, key: str) -> Path:
        normalized_key = _normalize_key(key)
        if not normalized_key:
            raise ValueError("Object key must be a non-empty path-like string.")
        return self._root.joinpath(*normalized_key.split("/"))


def _normalize_key(key: str) -> str:
    candidate = key.strip().strip("/")
    if ".." in candidate.split("/"):
        raise ValueError("Object key cannot contain parent directory traversal segments.")
    return candidate
