"""List and detail routes for published agents."""

from __future__ import annotations

import importlib
from typing import Any

from starlette.requests import Request

from server.auth.middleware import authenticate_request
from server.auth.token import TokenClaims, TokenService
from server.metadata.manager import MetadataManager
from server.routes.errors import build_error_envelope, resolve_request_id
from server.storage.base import StorageBackend


def list_agents_payload(
    *,
    authorization_header: str | None,
    token_service: TokenService,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    session_cookie_value: str | None,
    session_service,
    user_store,
    offset: int,
    limit: int,
    tenant_filter: str | None,
) -> tuple[int, dict[str, object]]:
    try:
        claims = authenticate_request(
            authorization_header=authorization_header,
            required_scope="registry:read",
            token_service=token_service,
            session_cookie_value=session_cookie_value,
            session_service=session_service,
            user_store=user_store,
        )
    except PermissionError as error:
        status = 403 if "403" in str(error) else 401
        return status, {"error": str(error)}

    if offset < 0:
        return 400, {"error": "offset must be >= 0"}
    if limit <= 0:
        return 400, {"error": "limit must be > 0"}

    global_index = metadata_manager.get_global_index()
    if global_index is None:
        return 200, {
            "items": [],
            "offset": offset,
            "limit": limit,
            "total": 0,
        }

    items: list[dict[str, object]] = []
    for tenant_slug, summaries in sorted(global_index.tenants.items(), key=lambda item: item[0]):
        if tenant_filter is not None and tenant_slug != tenant_filter:
            continue

        for summary in summaries:
            if not _can_read_tenant(claims=claims, tenant_slug=tenant_slug, visibility=summary.visibility):
                continue
            items.append(
                {
                    "tenant_slug": tenant_slug,
                    "name": summary.agent_slug,
                    "agent_slug": summary.agent_slug,
                    "visibility": summary.visibility,
                    "latest_version": summary.latest_version,
                    "latest_updated_at": summary.latest_updated_at,
                    "description": _description_for_summary(
                        metadata_manager=metadata_manager,
                        tenant_slug=tenant_slug,
                        agent_slug=summary.agent_slug,
                        version=summary.latest_version,
                    ),
                    "author": _author_for_summary(
                        metadata_manager=metadata_manager,
                        tenant_slug=tenant_slug,
                        agent_slug=summary.agent_slug,
                        version=summary.latest_version,
                    ),
                    "archive_size_bytes": _archive_size_for_summary(
                        metadata_manager=metadata_manager,
                        storage_backend=storage_backend,
                        tenant_slug=tenant_slug,
                        agent_slug=summary.agent_slug,
                        version=summary.latest_version,
                    ),
                }
            )

    total = len(items)
    page = items[offset : offset + limit]
    return 200, {
        "items": page,
        "offset": offset,
        "limit": limit,
        "total": total,
    }


def agent_detail_payload(
    *,
    authorization_header: str | None,
    token_service: TokenService,
    metadata_manager: MetadataManager,
    session_cookie_value: str | None,
    session_service,
    user_store,
    tenant_slug: str,
    agent_slug: str,
) -> tuple[int, dict[str, object]]:
    try:
        claims = authenticate_request(
            authorization_header=authorization_header,
            required_scope="registry:read",
            token_service=token_service,
            session_cookie_value=session_cookie_value,
            session_service=session_service,
            user_store=user_store,
        )
    except PermissionError as error:
        status = 403 if "403" in str(error) else 401
        return status, {"error": str(error)}

    agent_index = metadata_manager.get_agent_index(tenant_slug=tenant_slug, agent_slug=agent_slug)
    if agent_index is None:
        return 404, {"error": f"Agent not found: {tenant_slug}/{agent_slug}"}

    if not _can_read_tenant(claims=claims, tenant_slug=tenant_slug, visibility=agent_index.visibility):
        return 403, {"error": "403 forbidden: private tenant access denied"}

    latest_version = _latest_version_from_index(agent_index=agent_index)
    agent_manifest: dict[str, object] = {}
    if latest_version:
        metadata = metadata_manager.get_version_metadata(
            tenant_slug=tenant_slug,
            agent_slug=agent_slug,
            version=latest_version,
        )
        if metadata is not None and isinstance(metadata.manifest, dict):
            agent_manifest = dict(metadata.manifest)

    return 200, {
        "tenant_slug": agent_index.tenant_slug,
        "agent_slug": agent_index.agent_slug,
        "visibility": agent_index.visibility,
        "versions": [version.to_document() for version in agent_index.versions],
        "latest_version": latest_version,
        "agent_manifest": agent_manifest,
        "schema_version": agent_index.schema_version,
    }


def create_agents_router(
    *,
    token_service: TokenService,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
) -> Any:
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")
    Header = getattr(fastapi_module, "Header")
    Query = getattr(fastapi_module, "Query")

    responses_module = importlib.import_module("fastapi.responses")
    JSONResponse = getattr(responses_module, "JSONResponse")

    router = APIRouter()

    @router.get("/api/agents")
    async def list_agents(
        request: Request,
        authorization: str | None = Header(default=None),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        tenant: str | None = Query(default=None),
    ) -> dict[str, object]:
        status, payload = list_agents_payload(
            authorization_header=authorization,
            token_service=token_service,
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
            session_cookie_value=request.cookies.get(request.app.state.session_service.cookie_name),
            session_service=request.app.state.session_service,
            user_store=request.app.state.user_store,
            offset=offset,
            limit=limit,
            tenant_filter=tenant,
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
        return payload

    @router.get("/api/agents/{tenant_slug}/{agent_slug}")
    async def get_agent_detail(
        request: Request,
        tenant_slug: str,
        agent_slug: str,
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        status, payload = agent_detail_payload(
            authorization_header=authorization,
            token_service=token_service,
            metadata_manager=metadata_manager,
            session_cookie_value=request.cookies.get(request.app.state.session_service.cookie_name),
            session_service=request.app.state.session_service,
            user_store=request.app.state.user_store,
            tenant_slug=tenant_slug,
            agent_slug=agent_slug,
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
        return payload

    return router


def _can_read_tenant(*, claims: TokenClaims, tenant_slug: str, visibility: str) -> bool:
    if visibility != "private":
        return True
    # V1 collaborator model is represented by tenant-scoped tokens.
    return claims.tenant_slug == tenant_slug


def _description_for_summary(
    *,
    metadata_manager: MetadataManager,
    tenant_slug: str,
    agent_slug: str,
    version: str,
) -> str:
    if not version:
        return ""
    metadata = metadata_manager.get_version_metadata(
        tenant_slug=tenant_slug,
        agent_slug=agent_slug,
        version=version,
    )
    if metadata is None:
        return ""
    return str(metadata.manifest.get("description", ""))


def _author_for_summary(
    *,
    metadata_manager: MetadataManager,
    tenant_slug: str,
    agent_slug: str,
    version: str,
) -> str:
    if not version:
        return ""
    metadata = metadata_manager.get_version_metadata(
        tenant_slug=tenant_slug,
        agent_slug=agent_slug,
        version=version,
    )
    if metadata is None:
        return ""
    return str(metadata.manifest.get("author", ""))


def _latest_version_from_index(*, agent_index) -> str:
    if not agent_index.versions:
        return ""
    latest = max(agent_index.versions, key=lambda item: item.updated_at)
    return latest.version


def _archive_size_for_summary(
    *,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    tenant_slug: str,
    agent_slug: str,
    version: str,
) -> int:
    if not version:
        return 0
    metadata = metadata_manager.get_version_metadata(
        tenant_slug=tenant_slug,
        agent_slug=agent_slug,
        version=version,
    )
    if metadata is None:
        return 0
    archive_key = metadata.storage_keys.get("archive")
    if not archive_key:
        return 0
    try:
        archive_bytes = storage_backend.get_object(key=archive_key)
    except FileNotFoundError:
        return 0
    return len(archive_bytes)
