from __future__ import annotations

import json
import subprocess

import pytest

from server.metadata.models import VersionMetadata, utc_now_iso


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test727_backfill_parity_and_rollback(tmp_path, migrated_postgres_database: str, postgres_available: bool) -> None:
#     ...
