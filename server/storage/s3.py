"""Real S3/MinIO storage backend implementation."""

from __future__ import annotations

import importlib
from typing import Any


class S3StorageBackend:
    """Store objects in S3-compatible backends via boto3."""

    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        s3_client: Any | None = None,
    ) -> None:
        self._bucket = bucket
        if s3_client is not None:
            self._client = s3_client
            return

        try:
            boto3_module = importlib.import_module("boto3")
        except ImportError as error:
            raise RuntimeError(
                "boto3 is required for S3StorageBackend. Install server/requirements.txt dependencies."
            ) from error

        self._client = boto3_module.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def put_object(self, *, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)

    def get_object(self, *, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except Exception as error:
            error_name = error.__class__.__name__
            error_code = (
                getattr(error, "response", {}).get("Error", {}).get("Code")
                if hasattr(error, "response")
                else None
            )
            if error_name in {"NoSuchKey", "NotFound"} or error_code in {"NoSuchKey", "404", "NotFound"}:
                raise FileNotFoundError(f"Object not found: {key}") from None
            raise
        body = response["Body"]
        return body.read() if hasattr(body, "read") else bytes(body)

    def list_objects(self, *, prefix: str = "") -> list[str]:
        response = self._client.list_objects_v2(Bucket=self._bucket, Prefix=prefix)
        contents = response.get("Contents", [])
        return [item["Key"] for item in contents if "Key" in item]

    def delete_object(self, *, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def generate_presigned_url(self, *, key: str, expires_in_seconds: int) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )
