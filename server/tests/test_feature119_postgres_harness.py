from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_feature119_test729_local_ci_harness() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    conftest = (ROOT / "server/tests/conftest.py").read_text(encoding="utf-8")
    assert "postgres:" in compose
    assert "POSTGRES_DB: kinnoo_registry" in compose
    assert "services:" in workflow and "postgres:" in workflow
    assert "REGISTRY_DATABASE_URL" in workflow
    assert "migrated_postgres_database" in conftest
