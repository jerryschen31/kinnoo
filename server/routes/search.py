"""Search endpoint for querying published agents by name/description."""

from __future__ import annotations

import importlib
from typing import Any

from starlette.requests import Request

from server.auth.token import TokenService
from server.metadata.manager import MetadataManager
from server.routes.errors import build_error_envelope, resolve_request_id
from server.middleware import validate_and_inject_user_context


def search_payload(
    *,
    request,
    authorization_header: str | None,
    token_service: TokenService,
    metadata_manager: MetadataManager,
    query: str,
    offset: int,
    limit: int,
) -> tuple[int, dict[str, object]]:
    try:
        claims = validate_and_inject_user_context(
            request=request,
            authorization_header=authorization_header,
            token_service=token_service,
            required_scope="registry:read",
            session_cookie_value=request.cookies.get(request.app.state.session_service.cookie_name),
            session_service=request.app.state.session_service,
            user_store=request.app.state.user_store,
        )
    except PermissionError as error:
        status = 403 if "403" in str(error) else 401
        return status, {"error": str(error)}

    if not query.strip():
        return 400, {"error": "q must be a non-empty string"}
    if offset < 0:
        return 400, {"error": "offset must be >= 0"}
    if limit <= 0:
        return 400, {"error": "limit must be > 0"}

    needle = query.lower()
    global_index = metadata_manager.get_global_index()
    if global_index is None:
        return 200, {"items": [], "offset": offset, "limit": limit, "total": 0}

    matches: list[dict[str, object]] = []
    for tenant_slug, summaries in sorted(global_index.tenants.items(), key=lambda item: item[0]):
        for summary in summaries:
            if summary.visibility == "private" and claims.tenant_slug != tenant_slug:
                continue

            name_match = needle in summary.agent_slug.lower()
            description = ""
            if summary.latest_version:
                metadata = metadata_manager.get_version_metadata(
                    tenant_slug=tenant_slug,
                    agent_slug=summary.agent_slug,
                    version=summary.latest_version,
                )
                if metadata is not None:
                    description = str(metadata.manifest.get("description", ""))

            description_match = needle in description.lower()
            if not (name_match or description_match):
                continue

            matches.append(
                {
                    "tenant_slug": tenant_slug,
                    "agent_slug": summary.agent_slug,
                    "visibility": summary.visibility,
                    "latest_version": summary.latest_version,
                    "latest_updated_at": summary.latest_updated_at,
                    "description": description,
                }
            )

    total = len(matches)
    return 200, {
        "items": matches[offset : offset + limit],
        "offset": offset,
        "limit": limit,
        "total": total,
    }


def create_search_router(*, token_service: TokenService, metadata_manager: MetadataManager) -> Any:
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")
    Header = getattr(fastapi_module, "Header")
    Query = getattr(fastapi_module, "Query")

    responses_module = importlib.import_module("fastapi.responses")
    JSONResponse = getattr(responses_module, "JSONResponse")

    router = APIRouter()

    @router.get("/api/search")
    async def search_agents(
        request: Request,
        q: str = Query(default=""),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        status, payload = search_payload(
            request=request,
            authorization_header=authorization,
            token_service=token_service,
            metadata_manager=metadata_manager,
            query=q,
            offset=offset,
            limit=limit,
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
