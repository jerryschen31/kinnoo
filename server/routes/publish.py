"""Publish endpoint implementation and route wrapper."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from io import BytesIO
import importlib
from typing import Any
import zipfile

from starlette.requests import Request
import yaml

from server.auth.middleware import authenticate_request
from server.auth.token import TokenService
from server.metadata.manager import MetadataManager
from server.metadata.models import VersionMetadata, utc_now_iso
from server.routes.errors import build_error_envelope, resolve_request_id
from server.storage.base import StorageBackend


@dataclass(frozen=True)
class PublishResult:
    status_code: int
    body: dict[str, object]


def publish_archive(
    *,
    authorization_header: str | None,
    filename: str,
    archive_bytes: bytes,
    token_service: TokenService,
    storage_backend: StorageBackend,
    metadata_manager: MetadataManager,
    max_upload_mb: int,
) -> PublishResult:
    try:
        claims = authenticate_request(
            authorization_header=authorization_header,
            required_scope="registry:publish",
            token_service=token_service,
        )
    except PermissionError as error:
        status_code = 403 if "403" in str(error) else 401
        return PublishResult(status_code=status_code, body={"error": str(error)})

    if not filename.endswith(".kno"):
        return PublishResult(status_code=400, body={"error": "archive must use .kno extension"})

    max_size_bytes = max_upload_mb * 1024 * 1024
    if len(archive_bytes) > max_size_bytes:
        return PublishResult(
            status_code=400,
            body={"error": f"archive exceeds max upload size ({max_upload_mb} MB)"},
        )

    manifest = _load_manifest_from_archive(archive_bytes)
    if manifest is None:
        return PublishResult(status_code=400, body={"error": "archive missing valid kinnoo.yaml"})

    agent_slug = str(manifest.get("name", "")).strip()
    version = str(manifest.get("version", "")).strip()
    if not agent_slug or not version:
        return PublishResult(status_code=400, body={"error": "manifest requires non-empty name and version"})

    tenant_slug = claims.tenant_slug

    existing = metadata_manager.get_version_metadata(
        tenant_slug=tenant_slug,
        agent_slug=agent_slug,
        version=version,
    )
    if existing is not None:
        return PublishResult(
            status_code=409,
            body={"error": f"Version already published for {tenant_slug}/{agent_slug}/{version}"},
        )

    archive_key = (
        f"archives/tenants/{tenant_slug}/agents/{agent_slug}/versions/{version}/{agent_slug}.kno"
    )
    checksum_key = archive_key + ".sha256"
    sha256_hex = hashlib.sha256(archive_bytes).hexdigest()

    storage_backend.put_object(
        key=archive_key,
        data=archive_bytes,
        content_type="application/octet-stream",
    )
    storage_backend.put_object(
        key=checksum_key,
        data=sha256_hex.encode("utf-8"),
        content_type="text/plain",
    )

    timestamp = utc_now_iso()
    version_metadata = VersionMetadata(
        tenant_slug=tenant_slug,
        agent_slug=agent_slug,
        version=version,
        visibility=str(manifest.get("visibility", "private")),
        manifest=manifest,
        storage_keys={
            "archive": archive_key,
            "checksum": checksum_key,
        },
        integrity={"sha256": sha256_hex},
        publisher={
            "user_id": claims.sub,
            "token_id": claims.token_id,
        },
        created_at=timestamp,
        updated_at=timestamp,
    )
    metadata_manager.upsert_version_metadata(version_metadata)

    return PublishResult(
        status_code=201,
        body={
            "tenant_slug": tenant_slug,
            "agent_slug": agent_slug,
            "version": version,
            "archive_key": archive_key,
            "checksum": sha256_hex,
        },
    )


def create_publish_router(
    *,
    token_service: TokenService,
    storage_backend: StorageBackend,
    metadata_manager: MetadataManager,
    max_upload_mb: int,
) -> Any:
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")
    File = getattr(fastapi_module, "File")
    Header = getattr(fastapi_module, "Header")

    responses_module = importlib.import_module("fastapi.responses")
    JSONResponse = getattr(responses_module, "JSONResponse")

    router = APIRouter()

    @router.post("/api/publish", status_code=201)
    async def publish_endpoint(
        request: Request,
        file=File(...),
        authorization: str | None = Header(default=None),
    ) -> dict[str, object]:
        payload = await file.read()
        result = publish_archive(
            authorization_header=authorization,
            filename=file.filename or "upload.kno",
            archive_bytes=payload,
            token_service=token_service,
            storage_backend=storage_backend,
            metadata_manager=metadata_manager,
            max_upload_mb=max_upload_mb,
        )
        # Route wrappers are thin; publish_archive carries all business logic.
        if result.status_code >= 400:
            return JSONResponse(
                status_code=result.status_code,
                content=build_error_envelope(
                    status_code=result.status_code,
                    message=str(result.body["error"]),
                    request_id=resolve_request_id(request),
                ),
            )
        return result.body

    return router


def _load_manifest_from_archive(archive_bytes: bytes) -> dict[str, object] | None:
    try:
        with zipfile.ZipFile(BytesIO(archive_bytes), "r") as archive:
            if "kinnoo.yaml" not in archive.namelist():
                return None
            raw_manifest = archive.read("kinnoo.yaml").decode("utf-8")
            parsed = yaml.safe_load(raw_manifest)
    except (zipfile.BadZipFile, OSError, UnicodeDecodeError, yaml.YAMLError):
        return None

    if not isinstance(parsed, dict):
        return None
    return parsed
