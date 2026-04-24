from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from server.database.repository import RegistryRepository
from server.database.session import create_database_runtime
from server.metadata.models import VersionMetadata, utc_now_iso
from server.metadata.postgres_manager import PostgresMetadataManager


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test730_publish_search_concurrency(migrated_postgres_database: str, postgres_available: bool) -> None:
#     ...
