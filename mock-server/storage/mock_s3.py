"""Mock S3 storage backend implementation using moto."""

from __future__ import annotations

from contextlib import AbstractContextManager
import importlib
from typing import Any

from server.storage.s3 import S3StorageBackend


class MockS3Backend(S3StorageBackend):
    """S3 backend that can run fully local via moto for tests/dev."""

    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        s3_client: Any | None = None,
    ) -> None:
        self._moto_context: AbstractContextManager[Any] | None = None

        if s3_client is None:
            try:
                moto_module = importlib.import_module("moto")
                boto3_module = importlib.import_module("boto3")
            except ImportError as error:
                raise RuntimeError(
                    "moto and boto3 are required for default MockS3Backend initialization."
                ) from error

            mock_aws = getattr(moto_module, "mock_aws")
            self._moto_context = mock_aws()
            self._moto_context.start()
            s3_client = boto3_module.client("s3", region_name=region)
            s3_client.create_bucket(Bucket=bucket)

        super().__init__(
            bucket=bucket,
            region=region,
            s3_client=s3_client,
        )

    def close(self) -> None:
        if self._moto_context is not None:
            self._moto_context.stop()
            self._moto_context = None

    def __del__(self) -> None:
        self.close()
