from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


# [agent] test used during UAT or migration, currently not used for regression
# def test_task496_dual_app_secret_wiring() -> None:
#     ...


# [agent] test used during UAT or migration, currently not used for regression
# def test_task496_dev_tfvars_and_cloudflare_runtime_contract() -> None:
#     ...
