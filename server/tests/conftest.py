from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from tests.marker_tools import apply_auto_markers, register_markers


def pytest_configure(config: pytest.Config) -> None:
    register_markers(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    apply_auto_markers(items)


@pytest.fixture(scope="session")
def postgres_database_url() -> str:
    return (os.getenv("REGISTRY_DATABASE_URL") or "postgresql+psycopg://kinnoo:kinnoo@127.0.0.1:5432/kinnoo_registry").strip()


@pytest.fixture(scope="session")
def postgres_available(postgres_database_url: str) -> bool:
    try:
        engine = create_engine(postgres_database_url, future=True, pool_pre_ping=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


@pytest.fixture(scope="session")
def migrated_postgres_database(postgres_database_url: str, postgres_available: bool) -> str:
    if not postgres_available:
        pytest.skip("Postgres is not available for feature119 integration tests.")
    alembic_ini = Path(__file__).resolve().parents[1] / "database" / "migrations" / "alembic.ini"
    env = dict(os.environ)
    env["REGISTRY_DATABASE_URL"] = postgres_database_url
    upgrade = subprocess.run(
        ["python3", "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if upgrade.returncode != 0:
        raise AssertionError(f"alembic upgrade failed:\n{upgrade.stdout}\n{upgrade.stderr}")
    yield postgres_database_url
    downgrade = subprocess.run(
        ["python3", "-m", "alembic", "-c", str(alembic_ini), "downgrade", "base"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if downgrade.returncode != 0:
        raise AssertionError(f"alembic downgrade failed:\n{downgrade.stdout}\n{downgrade.stderr}")
