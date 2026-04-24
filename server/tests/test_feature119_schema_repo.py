from __future__ import annotations

from sqlalchemy import create_engine, inspect

from server.database.repository import RegistryRepository
from server.database.session import create_database_runtime
from server.metadata.models import VersionMetadata, utc_now_iso


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test723_schema_and_repository_contract(migrated_postgres_database: str) -> None:
#     ...
