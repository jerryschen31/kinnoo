"""Web UI routes for authenticated agent listing and search pages."""

from __future__ import annotations

import importlib
from typing import Any

from starlette.requests import Request

from server.metadata.manager import MetadataManager
from server.storage.base import StorageBackend


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def create_web_agents_router(
    *,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
) -> Any:
    """Create web UI router for listing and searching published agents."""
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")
    Query = getattr(fastapi_module, "Query")

    responses_module = importlib.import_module("fastapi.responses")
    HTMLResponse = getattr(responses_module, "HTMLResponse")
    RedirectResponse = getattr(responses_module, "RedirectResponse")

    router = APIRouter()

    @router.get("/agents", response_class=HTMLResponse)
    async def agents_page(
        request: Request,
        page: int = Query(default=1, ge=1),
        per_page: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    ) -> HTMLResponse:
        items = _all_agent_rows(
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
        )
        total = len(items)
        start = (page - 1) * per_page
        page_items = items[start : start + per_page]

        has_prev = page > 1
        has_next = start + per_page < total

        return request.app.state.templates.TemplateResponse(
            request=request,
            name="agents.html",
            context={
                "agents": page_items,
                "page": page,
                "per_page": per_page,
                "total": total,
                "has_prev": has_prev,
                "has_next": has_next,
                "prev_page": max(page - 1, 1),
                "next_page": page + 1,
            },
        )

    @router.get("/search", response_class=HTMLResponse)
    async def search_page(
        request: Request,
        q: str = Query(default=""),
    ) -> HTMLResponse:
        all_items = _all_agent_rows(
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
        )

        query = q.strip()
        if not query:
            results: list[dict[str, object]] = []
        else:
            needle = query.lower()
            results = [
                item
                for item in all_items
                if needle in str(item["name"]).lower() or needle in str(item["description"]).lower()
            ]

        return request.app.state.templates.TemplateResponse(
            request=request,
            name="search.html",
            context={
                "query": query,
                "results": results,
                "total": len(results),
            },
        )

    @router.get("/agents/{tenant_slug}/{agent_slug}", response_class=HTMLResponse)
    async def agent_profile_page(
        request: Request,
        tenant_slug: str,
        agent_slug: str,
    ) -> HTMLResponse:
        profile = _build_agent_profile(
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
            tenant_slug=tenant_slug,
            agent_slug=agent_slug,
        )
        if profile is None:
            return HTMLResponse("Agent not found", status_code=404)

        return request.app.state.templates.TemplateResponse(
            request=request,
            name="agent_profile.html",
            context={
                "profile": profile,
            },
        )

    @router.get("/agents/{tenant_slug}/{agent_slug}/{version}/download")
    async def agent_download_redirect(
        request: Request,
        tenant_slug: str,
        agent_slug: str,
        version: str,
    ) -> Any:
        metadata = metadata_manager.get_version_metadata(
            tenant_slug=tenant_slug,
            agent_slug=agent_slug,
            version=version,
        )
        if metadata is None:
            return HTMLResponse("Version not found", status_code=404)

        archive_key = str(metadata.storage_keys.get("archive", ""))
        if not archive_key:
            return HTMLResponse("Archive missing", status_code=404)

        presigned = storage_backend.generate_presigned_url(
            key=archive_key,
            expires_in_seconds=int(request.app.state.config.presign_ttl_seconds),
        )
        return RedirectResponse(url=presigned, status_code=303)

    return router


def _all_agent_rows(*, metadata_manager: MetadataManager, storage_backend: StorageBackend) -> list[dict[str, object]]:
    global_index = metadata_manager.get_global_index()
    if global_index is None:
        return []

    rows: list[dict[str, object]] = []
    for tenant_slug, summaries in sorted(global_index.tenants.items(), key=lambda item: item[0]):
        for summary in summaries:
            description = ""
            author = ""
            size_bytes = 0

            latest_version = summary.latest_version
            if latest_version:
                metadata = metadata_manager.get_version_metadata(
                    tenant_slug=tenant_slug,
                    agent_slug=summary.agent_slug,
                    version=latest_version,
                )
                if metadata is not None:
                    description = str(metadata.manifest.get("description", ""))
                    author = str(metadata.manifest.get("author", ""))

                    archive_key = metadata.storage_keys.get("archive")
                    if archive_key:
                        try:
                            archive = storage_backend.get_object(key=str(archive_key))
                            size_bytes = len(archive)
                        except FileNotFoundError:
                            size_bytes = 0

            rows.append(
                {
                    "tenant": tenant_slug,
                    "name": summary.agent_slug,
                    "version": latest_version,
                    "author": author,
                    "size_bytes": size_bytes,
                    "size_display": _format_size(size_bytes),
                    "description": description,
                    "visibility": summary.visibility,
                }
            )

    rows.sort(key=lambda item: (str(item["tenant"]), str(item["name"])))
    return rows


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _build_agent_profile(
    *,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    tenant_slug: str,
    agent_slug: str,
) -> dict[str, object] | None:
    agent_index = metadata_manager.get_agent_index(tenant_slug=tenant_slug, agent_slug=agent_slug)
    if agent_index is None:
        return None

    version_rows: list[dict[str, object]] = []
    latest_description = ""
    latest_author = ""

    sorted_versions = sorted(agent_index.versions, key=lambda item: item.version, reverse=True)
    for version_summary in sorted_versions:
        metadata = metadata_manager.get_version_metadata(
            tenant_slug=tenant_slug,
            agent_slug=agent_slug,
            version=version_summary.version,
        )

        description = ""
        author = ""
        archive_size_bytes = 0
        if metadata is not None:
            description = str(metadata.manifest.get("description", ""))
            author = str(metadata.manifest.get("author", ""))
            if not latest_description:
                latest_description = description
            if not latest_author:
                latest_author = author

            archive_key = metadata.storage_keys.get("archive")
            if archive_key:
                try:
                    archive_size_bytes = len(storage_backend.get_object(key=str(archive_key)))
                except FileNotFoundError:
                    archive_size_bytes = 0

        version_rows.append(
            {
                "version": version_summary.version,
                "created_at": version_summary.created_at,
                "updated_at": version_summary.updated_at,
                "description": description,
                "author": author,
                "size_bytes": archive_size_bytes,
                "size_display": _format_size(archive_size_bytes),
                "download_path": f"/agents/{tenant_slug}/{agent_slug}/{version_summary.version}/download",
            }
        )

    latest_version = version_rows[0]["version"] if version_rows else ""
    return {
        "tenant_slug": tenant_slug,
        "agent_slug": agent_slug,
        "visibility": agent_index.visibility,
        "latest_version": latest_version,
        "total_versions": len(version_rows),
        "description": latest_description,
        "author": latest_author,
        "versions": version_rows,
    }
