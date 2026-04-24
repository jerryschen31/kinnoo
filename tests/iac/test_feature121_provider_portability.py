"""task521 / test744: terraform provider portability (no hardcoded profile)."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.regression_integration
@pytest.mark.ops
def test_feature121_test744_provider_profile_portability() -> None:
    providers_tf = (ROOT / "iac" / "providers.tf").read_text(encoding="utf-8")
    state_tf = (ROOT / "iac" / "state" / "main.tf").read_text(encoding="utf-8")

    # Hardcoded operator profile must not appear anywhere.
    assert 'profile = "jerry"' not in providers_tf
    assert 'profile = "jerry"' not in state_tf

    # No `profile = "..."` literal in either provider block (rely on the
    # standard AWS credential chain instead).
    for text, label in ((providers_tf, "iac/providers.tf"), (state_tf, "iac/state/main.tf")):
        for line in text.splitlines():
            stripped = line.split("#", 1)[0].strip()
            if stripped.startswith("profile") and "=" in stripped:
                raise AssertionError(
                    f"{label} still pins an AWS profile literal: {stripped!r}"
                )

    # Provider block still configures region; portability change shouldn't
    # accidentally drop region wiring.
    assert "region = var.aws_region" in providers_tf
    assert "region = var.aws_region" in state_tf
