"""Download endpoint that returns presigned archive URLs."""

from __future__ import annotations

import importlib
from typing import Any

from server.auth.middleware import authenticate_request
from server.auth.token import TokenClaims, TokenService
from server.metadata.manager import MetadataManager
from server.storage.base import StorageBackend


def download_payload(
    *,
    authorization_header: str | None,
    token_service: TokenService,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    tenant_slug: str,
    agent_slug: str,
    version: str,
    presign_ttl_seconds: int,
) -> tuple[int, dict[str, object]]:
    try:
        claims = authenticate_request(
            authorization_header=authorization_header,
            required_scope="registry:read",
            token_service=token_service,
        )
    except PermissionError as error:
        status = 403 if "403" in str(error) else 401
        return status, {"error": str(error)}

    metadata = metadata_manager.get_version_metadata(
        tenant_slug=tenant_slug,
        agent_slug=agent_slug,
        version=version,
    )
    if metadata is None:
        return 404, {"error": f"Version not found: {tenant_slug}/{agent_slug}/{version}"}

    if not _can_read_tenant(claims=claims, tenant_slug=tenant_slug, visibility=metadata.visibility):
        return 403, {"error": "403 forbidden: private tenant access denied"}

    archive_key = metadata.storage_keys.get("archive")
    if not archive_key:
        return 404, {"error": "Archive object missing for requested version."}

    download_url = storage_backend.generate_presigned_url(
        key=archive_key,
        expires_in_seconds=presign_ttl_seconds,
    )
    return 200, {
        "download_url": download_url,
        "expires_in": presign_ttl_seconds,
        "tenant_slug": tenant_slug,
        "agent_slug": agent_slug,
        "version": version,
    }


def create_download_router(
    *,
    token_service: TokenService,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    presign_ttl_seconds: int,
) -> Any:
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")
    Header = getattr(fastapi_module, "Header")
    HTTPException = getattr(fastapi_module, "HTTPException")

    router = APIRouter()

    @router.get("/api/agents/{tenant_slug}/{agent_slug}/{version}/download")
    async def download_archive(
        tenant_slug: str,
        agent_slug: str,
        version: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        status, payload = download_payload(
            authorization_header=authorization,
            token_service=token_service,
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
            tenant_slug=tenant_slug,
            agent_slug=agent_slug,
            version=version,
            presign_ttl_seconds=presign_ttl_seconds,
        )
        if status >= 400:
            raise HTTPException(status_code=status, detail=payload["error"])
        return payload

    return router


def _can_read_tenant(*, claims: TokenClaims, tenant_slug: str, visibility: str) -> bool:
    if visibility != "private":
        return True
    return claims.tenant_slug == tenant_slug
