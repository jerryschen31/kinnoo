"""Remote registry client implementation backed by urllib.request."""

from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from typing import Any, Optional
from urllib import parse as urllib_parse
from urllib import request as urllib_request


class RemoteRegistryClient:
    """HTTP client that implements registry backend semantics for remote servers."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        tenant_slug: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        normalized_base_url = base_url.strip().rstrip("/")
        if not normalized_base_url:
            raise ValueError("base_url must be a non-empty string")
        if not token.strip():
            raise ValueError("token must be a non-empty string")
        if not tenant_slug.strip():
            raise ValueError("tenant_slug must be a non-empty string")

        self._base_url = normalized_base_url
        self._token = token.strip()
        self._tenant_slug = tenant_slug.strip()
        self._timeout_seconds = timeout_seconds

    def publish(
        self,
        *,
        name: str,
        version: str,
        archive_path: Path,
        manifest_metadata: Optional[dict[str, Any]] = None,
        tenant: str | None = None,
    ) -> dict[str, Any]:
        """Upload archive payload to remote publish endpoint using multipart form data."""
        effective_tenant = self._effective_tenant(tenant)
        file_bytes = Path(archive_path).read_bytes()
        metadata_payload = manifest_metadata or {}
        body, content_type = _encode_multipart_form_data(
            fields={
                "tenant_slug": effective_tenant,
                "name": name,
                "version": version,
                "metadata": json.dumps(metadata_payload, sort_keys=True),
            },
            file_field_name="archive",
            filename=Path(archive_path).name,
            file_bytes=file_bytes,
        )

        return self._request_json(
            method="POST",
            path="/api/publish",
            body=body,
            extra_headers={"Content-Type": content_type},
        )

    def resolve(
        self,
        *,
        name: str,
        version: Optional[str] = None,
        tenant: str | None = None,
    ) -> dict[str, Any]:
        """Fetch remote download metadata for an agent version."""
        effective_tenant = self._effective_tenant(tenant)
        selected_version = version or "latest"
        encoded_tenant = urllib_parse.quote(effective_tenant, safe="")
        encoded_name = urllib_parse.quote(name, safe="")
        encoded_version = urllib_parse.quote(selected_version, safe="")
        path = f"/api/agents/{encoded_tenant}/{encoded_name}/{encoded_version}/download"
        return self._request_json(method="GET", path=path)

    def search(self, *, query: str, tenant: str | None = None) -> list[dict[str, Any]]:
        """Search agents by name/description on remote registry."""
        _ = tenant
        encoded_query = urllib_parse.quote(query)
        response = self._request_json(method="GET", path=f"/api/search?q={encoded_query}")
        if isinstance(response, list):
            return response
        return response.get("items", []) if isinstance(response, dict) else []

    def list_agents(self, *, tenant: str | None = None) -> list[dict[str, Any]]:
        """List agents for a tenant on remote registry."""
        effective_tenant = self._effective_tenant(tenant)
        encoded_tenant = urllib_parse.quote(effective_tenant)
        response = self._request_json(method="GET", path=f"/api/agents?tenant={encoded_tenant}")
        if isinstance(response, list):
            return response
        return response.get("items", []) if isinstance(response, dict) else []

    # Compatibility methods to satisfy the broader registry protocol shape used
    # by existing service code until remote CLI selection is introduced in task232.
    def list_entries(self) -> list[dict[str, Any]]:
        return self.list_agents()

    def list_latest_agents(self) -> list[dict[str, Any]]:
        return self.list_agents()

    def search_agents(self, *, query: str) -> list[dict[str, Any]]:
        return self.search(query=query)

    def _effective_tenant(self, tenant: str | None) -> str:
        return tenant.strip() if isinstance(tenant, str) and tenant.strip() else self._tenant_slug

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        body: bytes | None = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)

        request = urllib_request.Request(
            url=url,
            data=body,
            headers=headers,
            method=method,
        )

        with urllib_request.urlopen(request, timeout=self._timeout_seconds) as response:
            raw_body = response.read().decode("utf-8")

        if not raw_body.strip():
            return {}

        decoded = json.loads(raw_body)
        return decoded


def _encode_multipart_form_data(
    *,
    fields: dict[str, str],
    file_field_name: str,
    filename: str,
    file_bytes: bytes,
) -> tuple[bytes, str]:
    """Encode multipart form payload for archive uploads."""

    boundary = f"kinnoo-{uuid.uuid4().hex}"
    content_type = f"multipart/form-data; boundary={boundary}"
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    body_parts: list[bytes] = []
    for key, value in fields.items():
        body_parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    body_parts.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{file_field_name}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )

    return b"".join(body_parts), content_type
