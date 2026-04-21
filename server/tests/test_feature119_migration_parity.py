from __future__ import annotations

import json
import subprocess

import pytest

from server.metadata.models import VersionMetadata, utc_now_iso


def test_feature119_test727_backfill_parity_and_rollback(tmp_path, migrated_postgres_database: str, postgres_available: bool) -> None:
    if not postgres_available:
        pytest.skip("Postgres is not available")

    now = utc_now_iso()
    metadata = VersionMetadata(
        tenant_slug="tenant-backfill",
        agent_slug="agent-backfill",
        version="1.2.3",
        visibility="private",
        manifest={"name": "agent-backfill", "version": "1.2.3"},
        storage_keys={"archive": "archives/tenant-backfill/agent-backfill/1.2.3.kno"},
        integrity={"sha256": "seed"},
        publisher={"user_id": "seed"},
        created_at=now,
        updated_at=now,
    )
    doc_path = tmp_path / "metadata" / "tenants" / "tenant-backfill" / "agents" / "agent-backfill" / "versions"
    doc_path.mkdir(parents=True, exist_ok=True)
    (doc_path / "1.2.3.v1.json").write_text(json.dumps(metadata.to_document(), indent=2), encoding="utf-8")

    backfill = subprocess.run(
        [
            "python3",
            "scripts/postgres_backfill.py",
            "--database-url",
            migrated_postgres_database,
            "--json-root",
            str(tmp_path / "metadata"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert backfill.returncode == 0, backfill.stdout + backfill.stderr

    backfill_again = subprocess.run(
        [
            "python3",
            "scripts/postgres_backfill.py",
            "--database-url",
            migrated_postgres_database,
            "--json-root",
            str(tmp_path / "metadata"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert backfill_again.returncode == 0, backfill_again.stdout + backfill_again.stderr

    parity = subprocess.run(
        [
            "python3",
            "scripts/postgres_parity.py",
            "--database-url",
            migrated_postgres_database,
            "--json-root",
            str(tmp_path / "metadata"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert parity.returncode == 0, parity.stdout + parity.stderr
    report = json.loads(parity.stdout)
    assert report["mismatch_count"] == 0
