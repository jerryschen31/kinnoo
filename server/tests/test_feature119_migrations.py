from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test724_alembic_upgrade_downgrade_cycle(postgres_database_url: str, postgres_available: bool) -> None:
#     ...
