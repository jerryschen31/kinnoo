"""Download endpoint that returns presigned archive URLs."""

from __future__ import annotations

import importlib
from urllib.parse import urlparse
from typing import Any

from starlette.requests import Request

from server.auth.middleware import authenticate_request
from server.auth.token import TokenClaims, TokenService
from server.metadata.manager import MetadataManager
from server.routes.errors import build_error_envelope, resolve_request_id
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

    responses_module = importlib.import_module("fastapi.responses")
    JSONResponse = getattr(responses_module, "JSONResponse")
    Response = getattr(responses_module, "Response")

    router = APIRouter()

    @router.get("/api/agents/{tenant_slug}/{agent_slug}/{version}/download")
    async def download_archive(
        request: Request,
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
            return JSONResponse(
                status_code=status,
                content=build_error_envelope(
                    status_code=status,
                    message=str(payload["error"]),
                    request_id=resolve_request_id(request),
                ),
            )

        # Local filesystem backends can emit file:// URLs that are not reachable
        # from remote CLI clients. Replace them with a token-authenticated API path.
        raw_download_url = payload.get("download_url") if isinstance(payload, dict) else None
        if isinstance(raw_download_url, str) and raw_download_url.strip():
            parsed = urlparse(raw_download_url.strip())
            if parsed.scheme == "file":
                direct_path = f"/api/agents/{tenant_slug}/{agent_slug}/{version}/archive"
                payload = dict(payload)
                payload["download_url"] = str(request.base_url).rstrip("/") + direct_path

        return payload

    @router.get("/api/agents/{tenant_slug}/{agent_slug}/{version}/archive")
    async def download_archive_bytes(
        request: Request,
        tenant_slug: str,
        agent_slug: str,
        version: str,
        authorization: str | None = Header(default=None),
    ) -> Any:
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
            return JSONResponse(
                status_code=status,
                content=build_error_envelope(
                    status_code=status,
                    message=str(payload["error"]),
                    request_id=resolve_request_id(request),
                ),
            )

        metadata = metadata_manager.get_version_metadata(
            tenant_slug=tenant_slug,
            agent_slug=agent_slug,
            version=version,
        )
        if metadata is None:
            return JSONResponse(
                status_code=404,
                content=build_error_envelope(
                    status_code=404,
                    message=f"Version not found: {tenant_slug}/{agent_slug}/{version}",
                    request_id=resolve_request_id(request),
                ),
            )

        archive_key = metadata.storage_keys.get("archive")
        if not archive_key:
            return JSONResponse(
                status_code=404,
                content=build_error_envelope(
                    status_code=404,
                    message="Archive object missing for requested version.",
                    request_id=resolve_request_id(request),
                ),
            )

        try:
            archive_bytes = storage_backend.get_object(key=str(archive_key))
        except FileNotFoundError:
            return JSONResponse(
                status_code=404,
                content=build_error_envelope(
                    status_code=404,
                    message="Archive object missing for requested version.",
                    request_id=resolve_request_id(request),
                ),
            )

        return Response(
            content=archive_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{agent_slug}.kno"',
            },
        )

    return router


def _can_read_tenant(*, claims: TokenClaims, tenant_slug: str, visibility: str) -> bool:
    if visibility != "private":
        return True
    return claims.tenant_slug == tenant_slug
