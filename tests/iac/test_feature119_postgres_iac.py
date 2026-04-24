from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test721_private_rds_posture() -> None:
#     ...


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test722_ecs_env_secret_wiring() -> None:
#     ...
