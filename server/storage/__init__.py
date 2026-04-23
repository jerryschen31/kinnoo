"""Storage adapters for remote registry server."""

from __future__ import annotations

from typing import Any

from server.config import ServerConfig

from .base import StorageBackend
from .local import LocalStorageBackend
from .s3 import S3StorageBackend


def build_storage_backend_from_config(
	config: ServerConfig,
	*,
	s3_client: Any | None = None,
) -> StorageBackend:
	if config.storage_backend == "local":
		return LocalStorageBackend(root=config.local_storage_root)
	if config.storage_backend == "s3":
		return S3StorageBackend(
			bucket=config.s3_bucket,
			region=config.s3_region,
			endpoint_url=config.s3_endpoint_url,
			access_key_id=config.s3_access_key_id,
			secret_access_key=config.s3_secret_access_key,
			s3_client=s3_client,
		)
	raise ValueError(f"Unsupported storage backend '{config.storage_backend}'.")


def build_storage_backend_from_env(*, s3_client: Any | None = None) -> StorageBackend:
	return build_storage_backend_from_config(ServerConfig.from_env(), s3_client=s3_client)


__all__ = [
	"StorageBackend",
	"LocalStorageBackend",
	"S3StorageBackend",
	"build_storage_backend_from_config",
	"build_storage_backend_from_env",
]
