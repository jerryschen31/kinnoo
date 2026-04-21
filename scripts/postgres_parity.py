#!/usr/bin/env python3
"""Generate deterministic parity report between JSON and Postgres metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from server.database.repository import RegistryRepository
from server.database.session import create_database_runtime


def _canonical_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Parity checker for JSON and Postgres metadata")
    parser.add_argument("--database-url", required=True, help="Postgres database URL")
    parser.add_argument("--json-root", default=".registry-storage/metadata", help="Path to JSON metadata root")
    args = parser.parse_args()

    runtime = create_database_runtime(
        database_url=args.database_url,
        pool_size=5,
        max_overflow=5,
        pool_recycle_seconds=1800,
    )
    repository = RegistryRepository(session_factory=runtime.sync_session_factory)

    json_docs: dict[tuple[str, str, str], dict] = {}
    for file_path in sorted(Path(args.json_root).glob("tenants/*/agents/*/versions/*.v1.json")):
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        key = (payload["tenant_slug"], payload["agent_slug"], payload["version"])
        json_docs[key] = payload

    mismatches: list[dict[str, str]] = []
    for key, payload in json_docs.items():
        tenant_slug, agent_slug, version = key
        row = repository.get_version_metadata(tenant_slug=tenant_slug, agent_slug=agent_slug, version=version)
        if row is None:
            mismatches.append({"key": "/".join(key), "reason": "missing_in_postgres"})
            continue
        if _canonical_hash(payload) != _canonical_hash(row.to_document()):
            mismatches.append({"key": "/".join(key), "reason": "payload_hash_mismatch"})

    report = {
        "json_document_count": len(json_docs),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
