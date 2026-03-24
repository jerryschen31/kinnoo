"""Storage backend protocol shared by local, mock S3, and real S3 adapters."""

from __future__ import annotations

from typing import Protocol


class StorageBackend(Protocol):
    """Object-storage protocol used by registry services."""

    def put_object(self, *, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        ...

    def get_object(self, *, key: str) -> bytes:
        ...

    def list_objects(self, *, prefix: str = "") -> list[str]:
        ...

    def delete_object(self, *, key: str) -> None:
        ...

    def generate_presigned_url(self, *, key: str, expires_in_seconds: int) -> str:
        ...
