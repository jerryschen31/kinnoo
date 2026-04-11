"""Web UI routes for authenticated agent listing and search pages."""

from __future__ import annotations

import importlib
import json
from typing import Any

from starlette.requests import Request

from server.metadata.manager import MetadataManager
from server.storage.base import StorageBackend


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Canonical schema-field list shown in the agents-page manifest details panel.
MANIFEST_SCHEMA_FIELDS: tuple[str, ...] = (
    "name",
    "version",
    "entrypoint",
    "runtime.language",
    "runtime.version",
    "runtime.type",
    "runtime.package_manager",
    "dependencies",
    "inputs.type",
    "inputs.required",
    "outputs.type",
    "framework",
    "model",
    "description",
    "author",
    "license",
    "env_vars",
    "assets.paths",
    "assets.bundle",
    "assets.max_bundle_size_mb",
    "channels",
    "skills",
    "state_dirs",
    "services",
    "permissions",
)


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
        selected_tenant: str = Query(default=""),
        selected_agent: str = Query(default=""),
        selected_tab: str = Query(default="manifest"),
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
        selected_manifest = _build_selected_agent_manifest_view(
            metadata_manager=metadata_manager,
            tenant_slug=selected_tenant,
            agent_slug=selected_agent,
        )
        selected_versions = _build_selected_agent_versions_view(
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
            tenant_slug=selected_tenant,
            agent_slug=selected_agent,
        )
        selected_security = _build_selected_agent_security_view(
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
            tenant_slug=selected_tenant,
            agent_slug=selected_agent,
        )

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
                "selected_tenant": selected_tenant,
                "selected_agent": selected_agent,
                "selected_tab": selected_tab,
                "selected_manifest": selected_manifest,
                "selected_versions": selected_versions,
                "selected_security": selected_security,
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
            framework = "N/A"
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
                    # Keep table rendering deterministic for manifests that omit optional framework.
                    framework_value = metadata.manifest.get("framework")
                    if framework_value not in (None, ""):
                        framework = str(framework_value)

                    archive_key = metadata.storage_keys.get("archive")
                    if archive_key:
                        try:
                            archive = storage_backend.get_object(key=str(archive_key))
                            size_bytes = len(archive)
                        except FileNotFoundError:
                            size_bytes = 0

            security_snapshot = _resolve_security_snapshot_for_version(
                metadata_manager=metadata_manager,
                storage_backend=storage_backend,
                tenant_slug=tenant_slug,
                agent_slug=summary.agent_slug,
                version=latest_version,
            )
            security_icons = _security_icons_for_status(security_snapshot.get("security_status"))

            rows.append(
                {
                    "tenant": tenant_slug,
                    "name": summary.agent_slug,
                    "version": latest_version,
                    "author": author,
                    "framework": framework,
                    "size_bytes": size_bytes,
                    "size_display": _format_size(size_bytes),
                    "description": description,
                    "visibility": summary.visibility,
                    "security_icons": security_icons,
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


def _security_status_for_latest_version(
    *,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    tenant_slug: str,
    agent_slug: str,
    version: str,
) -> object:
    snapshot = _resolve_security_snapshot_for_version(
        metadata_manager=metadata_manager,
        storage_backend=storage_backend,
        tenant_slug=tenant_slug,
        agent_slug=agent_slug,
        version=version,
    )
    return snapshot.get("security_status", "")


def _security_icons_for_status(security_status: object) -> str:
    if isinstance(security_status, dict):
        verdicts = {
            "signature": str(security_status.get("signature", "")).strip().lower(),
            "archive": str(security_status.get("archive", "")).strip().lower(),
            "archive_integrity": str(security_status.get("archive_integrity", "")).strip().lower(),
            "per_file": str(security_status.get("per_file", "")).strip().lower(),
            "per_file_integrity": str(security_status.get("per_file_integrity", "")).strip().lower(),
        }
        if any(value == "fail" for value in verdicts.values() if value):
            return "❌"

        icons: list[str] = []
        if verdicts["signature"] == "pass":
            icons.append("✅")
        if verdicts["signature"] == "unsigned":
            # Unsigned artifacts should not be rendered as failures.
            pass
        if (
            verdicts["archive"] == "pass"
            or verdicts["archive_integrity"] == "pass"
        ):
            icons.append("📦")
        if (
            verdicts["per_file"] == "pass"
            or verdicts["per_file_integrity"] == "pass"
        ):
            icons.append("🧩")
        return "".join(icons)

    if not isinstance(security_status, str):
        return ""

    normalized = security_status.strip().lower()
    if not normalized:
        return ""
    if "fail" in normalized:
        return "❌"
    if "unsigned" in normalized:
        return ""

    aliases = {
        "signed_verified": "✅",
        "signature_pass": "✅",
        "archive_verified": "📦",
        "archive_pass": "📦",
        "file_integrity_verified": "🧩",
        "per_file_pass": "🧩",
    }
    if normalized in aliases:
        return aliases[normalized]

    icons: list[str] = []
    if "signed" in normalized or "signature" in normalized:
        icons.append("✅")
    if "archive" in normalized:
        icons.append("📦")
    if "file" in normalized or "per_file" in normalized:
        icons.append("🧩")
    return "".join(icons)


def _default_lambda_report_key(*, tenant_slug: str, agent_slug: str, version: str) -> str:
    return f"security-check/tenants/{tenant_slug}/agents/{agent_slug}/versions/{version}/report.json"


def _resolve_security_snapshot_for_version(
    *,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    tenant_slug: str,
    agent_slug: str,
    version: str,
) -> dict[str, object]:
    if not version:
        return {"security_status": "", "checks": []}

    report_key = _default_lambda_report_key(
        tenant_slug=tenant_slug,
        agent_slug=agent_slug,
        version=version,
    )

    try:
        report_bytes = storage_backend.get_object(key=report_key)
    except FileNotFoundError:
        return {"security_status": "", "checks": [], "report_key": report_key, "source": "none"}

    try:
        report_doc = json.loads(report_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"security_status": "", "checks": [], "report_key": report_key, "source": "invalid"}

    report_payload = report_doc.get("report") if isinstance(report_doc, dict) else None
    if not isinstance(report_payload, dict):
        return {"security_status": "", "checks": [], "report_key": report_key, "source": "invalid"}

    security_status = report_payload.get("security_status", "")
    checks_raw = report_payload.get("checks", [])
    checks: list[dict[str, str]] = []
    if isinstance(checks_raw, list):
        for item in checks_raw:
            if not isinstance(item, dict):
                continue
            checks.append(
                {
                    "check_name": str(item.get("check_name", "")),
                    "status": str(item.get("status", "")).lower(),
                    "detail": str(item.get("detail", "")),
                }
            )

    # Keep status shape stable for renderers even if upstream report is malformed.
    if not isinstance(security_status, (dict, str)):
        security_status = ""

    return {
        "security_status": security_status,
        "checks": checks,
        "report_key": report_key,
        "source": "lambda-report",
    }


def _resolve_manifest_path(manifest: dict[str, object], path: str) -> object | None:
    current: object = manifest
    for segment in path.split("."):
        if not isinstance(current, dict):
            return None
        if segment not in current:
            return None
        current = current[segment]
    return current


def _format_manifest_value(value: object | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _build_selected_agent_manifest_view(
    *,
    metadata_manager: MetadataManager,
    tenant_slug: str,
    agent_slug: str,
) -> dict[str, object] | None:
    normalized_tenant = tenant_slug.strip()
    normalized_agent = agent_slug.strip()
    if not normalized_tenant or not normalized_agent:
        return None

    profile = _build_agent_profile(
        metadata_manager=metadata_manager,
        storage_backend=None,
        tenant_slug=normalized_tenant,
        agent_slug=normalized_agent,
    )
    if profile is None:
        return None

    latest_version = str(profile.get("latest_version", "")).strip()
    if not latest_version:
        return None

    metadata = metadata_manager.get_version_metadata(
        tenant_slug=normalized_tenant,
        agent_slug=normalized_agent,
        version=latest_version,
    )
    if metadata is None:
        return None

    manifest_payload = metadata.manifest if isinstance(metadata.manifest, dict) else {}
    rows = [
        {
            "field": field,
            "value": _format_manifest_value(_resolve_manifest_path(manifest_payload, field)),
        }
        for field in MANIFEST_SCHEMA_FIELDS
    ]

    return {
        "tenant": normalized_tenant,
        "name": normalized_agent,
        "version": latest_version,
        "rows": rows,
    }


def _build_selected_agent_security_view(
    *,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    tenant_slug: str,
    agent_slug: str,
) -> dict[str, object] | None:
    normalized_tenant = tenant_slug.strip()
    normalized_agent = agent_slug.strip()
    if not normalized_tenant or not normalized_agent:
        return None

    profile = _build_agent_profile(
        metadata_manager=metadata_manager,
        storage_backend=None,
        tenant_slug=normalized_tenant,
        agent_slug=normalized_agent,
    )
    if profile is None:
        return None

    latest_version = str(profile.get("latest_version", "")).strip()
    if not latest_version:
        return None

    security_snapshot = _resolve_security_snapshot_for_version(
        metadata_manager=metadata_manager,
        storage_backend=storage_backend,
        tenant_slug=normalized_tenant,
        agent_slug=normalized_agent,
        version=latest_version,
    )

    return {
        "tenant": normalized_tenant,
        "name": normalized_agent,
        "version": latest_version,
        "checks": security_snapshot.get("checks", []),
        "source": security_snapshot.get("source", "none"),
        "report_key": security_snapshot.get("report_key", ""),
    }


def _build_selected_agent_versions_view(
    *,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend,
    tenant_slug: str,
    agent_slug: str,
) -> dict[str, object] | None:
    normalized_tenant = tenant_slug.strip()
    normalized_agent = agent_slug.strip()
    if not normalized_tenant or not normalized_agent:
        return None

    profile = _build_agent_profile(
        metadata_manager=metadata_manager,
        storage_backend=storage_backend,
        tenant_slug=normalized_tenant,
        agent_slug=normalized_agent,
    )
    if profile is None:
        return None

    return {
        "tenant": normalized_tenant,
        "name": normalized_agent,
        "versions": profile.get("versions", []),
    }


def _build_agent_profile(
    *,
    metadata_manager: MetadataManager,
    storage_backend: StorageBackend | None,
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
            if archive_key and storage_backend is not None:
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
