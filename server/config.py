"""Configuration helpers for registry server runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Literal


StorageBackendName = Literal["local", "mock", "s3"]


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer.") from error
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return value


@dataclass(frozen=True)
class ServerConfig:
    """Runtime configuration loaded from environment variables."""

    storage_backend: StorageBackendName
    local_storage_root: Path
    s3_bucket: str
    s3_region: str
    s3_endpoint_url: str | None
    s3_access_key_id: str | None
    s3_secret_access_key: str | None
    presign_ttl_seconds: int
    max_upload_mb: int
    registry_admin_email: str | None = None
    registry_admin_password: str | None = None

    @classmethod
    def from_env(cls) -> "ServerConfig":
        backend_raw = os.getenv("REGISTRY_STORAGE_BACKEND", "local").strip().lower()
        if backend_raw not in {"local", "mock", "s3"}:
            raise ValueError("REGISTRY_STORAGE_BACKEND must be one of: local, mock, s3")

        local_storage_root = Path(
            os.getenv("REGISTRY_LOCAL_STORAGE_ROOT", ".registry-storage")
        ).expanduser()

        return cls(
            storage_backend=backend_raw,
            local_storage_root=local_storage_root,
            s3_bucket=os.getenv("REGISTRY_S3_BUCKET", "kinnoo-registry-dev").strip(),
            s3_region=os.getenv("REGISTRY_S3_REGION", "us-east-1").strip(),
            s3_endpoint_url=os.getenv("REGISTRY_S3_ENDPOINT_URL") or None,
            s3_access_key_id=os.getenv("REGISTRY_S3_ACCESS_KEY_ID") or None,
            s3_secret_access_key=os.getenv("REGISTRY_S3_SECRET_ACCESS_KEY") or None,
            presign_ttl_seconds=_read_int_env("REGISTRY_PRESIGN_TTL_SECONDS", 900),
            max_upload_mb=_read_int_env("REGISTRY_MAX_UPLOAD_MB", 50),
            registry_admin_email=(os.getenv("REGISTRY_ADMIN_EMAIL") or "").strip() or None,
            registry_admin_password=os.getenv("REGISTRY_ADMIN_PASSWORD") or None,
        )
