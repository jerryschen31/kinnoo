"""task523 / test746: prod lambda image bootstrap script behavior."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "build_and_push_lambda_security_check_image.sh"


@pytest.mark.regression_integration
@pytest.mark.ops
def test_feature121_test746_prod_lambda_bootstrap(tmp_path: Path) -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    # Documents the targeted-apply trick using module.ecr.
    assert "-target=module.ecr" in text
    # Knows about the prod environment selector.
    assert '--env' in text
    assert 'ENVIRONMENT' in text
    # Backwards compatible default to dev.
    assert 'ENVIRONMENT="${ENVIRONMENT:-dev}"' in text

    # Dry-run against prod should print a prod-prefixed image URI suggestion
    # without invoking docker or aws. Stub terraform/docker/aws on PATH so
    # accidental real calls would fail loudly.
    bash = shutil.which("bash")
    assert bash is not None

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for cmd in ("terraform", "docker", "aws"):
        stub = fake_bin / cmd
        stub.write_text("#!/usr/bin/env bash\nexit 99\n")
        stub.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["DRY_RUN"] = "1"

    result = subprocess.run(
        [bash, str(SCRIPT), "--env", "prod", "v1"],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "kinnoo-prod-lambda-security-check" in combined
    assert "lambda_security_check_image_uri" in combined
    # Must not silently target dev when the operator selected prod.
    assert "kinnoo-dev-lambda-security-check" not in combined

    # And dev mode in dry-run should target dev, not prod.
    result_dev = subprocess.run(
        [bash, str(SCRIPT), "--env", "dev", "v1"],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    combined_dev = result_dev.stdout + result_dev.stderr
    assert result_dev.returncode == 0, combined_dev
    assert "kinnoo-dev-lambda-security-check" in combined_dev
    assert "kinnoo-prod-lambda-security-check" not in combined_dev
