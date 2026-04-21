#!/usr/bin/env python3
"""Backfill JSON metadata documents into Postgres metadata tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from server.database.repository import RegistryRepository
from server.database.session import create_database_runtime
from server.metadata.models import VersionMetadata
from server.metadata.postgres_manager import PostgresMetadataManager


def iter_metadata_documents(metadata_root: Path):
    pattern = metadata_root.glob("tenants/*/agents/*/versions/*.v1.json")
    for path in sorted(pattern):
        payload = json.loads(path.read_text(encoding="utf-8"))
        yield VersionMetadata.from_document(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill JSON metadata into Postgres")
    parser.add_argument("--database-url", required=True, help="Postgres database URL")
    parser.add_argument(
        "--json-root",
        default=".registry-storage/metadata",
        help="Path to existing JSON metadata root",
    )
    args = parser.parse_args()

    runtime = create_database_runtime(
        database_url=args.database_url,
        pool_size=10,
        max_overflow=20,
        pool_recycle_seconds=1800,
    )
    repository = RegistryRepository(session_factory=runtime.sync_session_factory)
    manager = PostgresMetadataManager(repository=repository)

    metadata_root = Path(args.json_root)
    if not metadata_root.exists():
        print(f"metadata root not found: {metadata_root}")
        return 1

    migrated = 0
    for metadata in iter_metadata_documents(metadata_root):
        manager.upsert_version_metadata(metadata)
        migrated += 1

    print(f"backfill_complete migrated={migrated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
