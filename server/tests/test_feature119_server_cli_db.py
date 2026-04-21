from __future__ import annotations

import pytest

from server.cli import main as server_cli_main


def test_feature119_test728_db_admin_commands(migrated_postgres_database: str, postgres_available: bool) -> None:
    if not postgres_available:
        pytest.skip("Postgres is not available")

    migrate_exit = server_cli_main(["db", "migrate", "--database-url", migrated_postgres_database])
    assert migrate_exit == 0

    seed_exit = server_cli_main(
        [
            "db",
            "seed",
            "--database-url",
            migrated_postgres_database,
            "--tenant-slug",
            "tenant-cli",
            "--agent-slug",
            "agent-cli",
            "--version",
            "0.0.1",
        ]
    )
    assert seed_exit == 0

    list_exit = server_cli_main(["db", "list", "agents", "--database-url", migrated_postgres_database])
    assert list_exit == 0
