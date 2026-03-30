"""Sync command implementation for ClawHub mirror ingestion."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .config import load_registry_config
from .registry import RegistryService
from .registry_backends import MockFilesystemRegistryBackend
from .remote_client import RemoteRegistryClient


def sync_source(
    *,
    source: str,
    full: bool = False,
    since: str | None = None,
    use_local: bool = False,
    use_remote: bool = False,
) -> int:
    normalized_source = source.strip().lower()
    if normalized_source != "clawhub":
        print(f"Error: Unsupported sync source '{source}'.")
        return 1

    if use_local and use_remote:
        print("Error: --local and --remote cannot be used together.")
        return 1

    registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
    backend_root = Path(registry_root).expanduser() if registry_root else None
    service = RegistryService(backend=MockFilesystemRegistryBackend(root=backend_root))

    records, fetch_error = _fetch_clawhub_sync_records(
        full=full,
        since=since,
        use_local=use_local,
        use_remote=use_remote,
    )
    if fetch_error is not None:
        print(f"Error: {fetch_error}")
        return 1

    created_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for raw_record in records:
        normalized_record, normalize_error = _normalize_sync_record(raw_record)
        if normalized_record is None:
            failed_count += 1
            reason = normalize_error or "invalid_sync_record"
            print(f"[kinnoo sync] warning: skipped invalid record ({reason})")
            continue

        agent_slug = normalized_record["agent_slug"]
        source_version = normalized_record["source_version"]
        source_url = normalized_record.get("source_url")
        synced_at = normalized_record.get("synced_at")
        metadata = normalized_record.get("metadata")

        existing = service.get_clawhub_mirror_record(agent_slug=agent_slug)
        if existing is not None and _mirror_record_matches(
            existing=existing,
            source_version=source_version,
            source_url=source_url,
            metadata=metadata,
        ):
            skipped_count += 1
            continue

        try:
            service.upsert_clawhub_mirror_record(
                agent_slug=agent_slug,
                source_version=source_version,
                source_url=source_url,
                synced_at=synced_at,
                metadata=metadata,
            )
        except Exception as error:  # pragma: no cover - defensive guard
            failed_count += 1
            print(
                "[kinnoo sync] warning: failed to upsert record "
                f"'{agent_slug}' ({type(error).__name__})"
            )
            continue

        if existing is None:
            created_count += 1
        else:
            updated_count += 1

    mode_label = "full" if full else "incremental"
    print(
        "[kinnoo sync] source=clawhub "
        f"mode={mode_label} "
        f"created={created_count} "
        f"updated={updated_count} "
        f"skipped={skipped_count} "
        f"failed={failed_count}"
    )
    return 0 if failed_count == 0 else 1


def _fetch_clawhub_sync_records(
    *,
    full: bool,
    since: str | None,
    use_local: bool,
    use_remote: bool,
) -> tuple[list[dict[str, Any]], str | None]:
    fixture_path_raw = os.environ.get("KINNOO_CLAWHUB_SYNC_FIXTURE")
    if fixture_path_raw:
        fixture_path = Path(fixture_path_raw).expanduser()
        if not fixture_path.exists() or not fixture_path.is_file():
            return [], f"ClawHub fixture file not found: {fixture_path}"

        try:
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return [], f"Failed to parse ClawHub fixture JSON: {error}"

        records = _extract_sync_records(payload)
        return records, None

    if use_local:
        return [], "Local sync mode requires KINNOO_CLAWHUB_SYNC_FIXTURE."

    config = load_registry_config()
    if not config.registry_url or not config.registry_token or not config.tenant_slug:
        return (
            [],
            "ClawHub sync source is not configured. "
            "Set KINNOO_CLAWHUB_SYNC_FIXTURE for local testing or configure remote registry auth.",
        )

    client = RemoteRegistryClient(
        base_url=config.registry_url,
        token=config.registry_token,
        tenant_slug=config.tenant_slug,
    )
    try:
        records = client.fetch_clawhub_mirror_index(full=full, since=since)
    except Exception as error:
        return [], str(error)

    del use_remote  # selection already resolved by configured remote auth path.
    return records, None


def _extract_sync_records(payload: object) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def _normalize_sync_record(raw_record: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    slug_candidates = (
        raw_record.get("agent_slug"),
        raw_record.get("source_slug"),
        raw_record.get("slug"),
    )
    version_candidates = (
        raw_record.get("source_version"),
        raw_record.get("version"),
    )

    agent_slug = _first_non_empty_str(slug_candidates)
    source_version = _first_non_empty_str(version_candidates)
    if agent_slug is None:
        return None, "missing_agent_slug"
    if source_version is None:
        return None, "missing_source_version"

    normalized: dict[str, Any] = {
        "agent_slug": agent_slug,
        "source_version": source_version,
    }

    source_url = _first_non_empty_str((raw_record.get("source_url"), raw_record.get("url")))
    if source_url is not None:
        normalized["source_url"] = source_url

    synced_at = _first_non_empty_str((raw_record.get("synced_at"),))
    if synced_at is not None:
        normalized["synced_at"] = synced_at

    metadata = raw_record.get("metadata")
    if isinstance(metadata, dict):
        normalized["metadata"] = metadata
    else:
        inferred_metadata = {
            key: value
            for key, value in raw_record.items()
            if key
            not in {
                "agent_slug",
                "source_slug",
                "slug",
                "source_version",
                "version",
                "source_url",
                "url",
                "synced_at",
                "metadata",
            }
        }
        normalized["metadata"] = inferred_metadata

    return normalized, None


def _first_non_empty_str(values: tuple[object, ...]) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _mirror_record_matches(
    *,
    existing: Any,
    source_version: str,
    source_url: str | None,
    metadata: dict[str, Any] | None,
) -> bool:
    existing_source_version = getattr(existing, "source_version", None)
    existing_source_url = getattr(existing, "source_url", None)
    existing_metadata = getattr(existing, "metadata", None)

    return (
        isinstance(existing_source_version, str)
        and existing_source_version == source_version
        and existing_source_url == source_url
        and isinstance(existing_metadata, dict)
        and isinstance(metadata, dict)
        and existing_metadata == metadata
    )