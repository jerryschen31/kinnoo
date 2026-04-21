from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest


def test_feature119_test724_alembic_upgrade_downgrade_cycle(postgres_database_url: str, postgres_available: bool) -> None:
    if not postgres_available:
        pytest.skip("Postgres is not available")
    alembic_ini = Path(__file__).resolve().parents[1] / "database" / "migrations" / "alembic.ini"
    env = dict(os.environ)
    env["REGISTRY_DATABASE_URL"] = postgres_database_url
    for command in (["upgrade", "head"], ["downgrade", "base"], ["upgrade", "head"]):
        result = subprocess.run(
            ["python3", "-m", "alembic", "-c", str(alembic_ini), *command],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
