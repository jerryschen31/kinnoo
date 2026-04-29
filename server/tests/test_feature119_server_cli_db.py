from __future__ import annotations

import pytest

from server.cli import main as server_cli_main


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test728_db_admin_commands(migrated_postgres_database: str, postgres_available: bool) -> None:
#     ...
