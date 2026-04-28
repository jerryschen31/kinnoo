"""task519 / test742: env-aware ops scripts contract."""
from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "ops"


def _read(rel_path: Path) -> str:
    return rel_path.read_text(encoding="utf-8")


@pytest.mark.regression_integration
@pytest.mark.ops
def test_feature121_test742_environment_safe_scripts(tmp_path: Path) -> None:
    rebuild = SCRIPTS / "rebuild_push_server_and_redeploy_ecs.sh"
    dns_check = SCRIPTS / "check_cloudflare_dns_setup.sh"
    lambda_build = SCRIPTS / "build_and_push_lambda_security_check_image.sh"

    rebuild_text = _read(rebuild)
    dns_text = _read(dns_check)
    lambda_text = _read(lambda_build)

    # No hardcoded dev cluster/service names.
    assert 'ECS_SERVICE="kinnoo-dev-service"' not in rebuild_text
    assert 'ECS_CLUSTER="kinnoo-dev-cluster"' not in rebuild_text
    assert "AWS_PROFILE:-jerry" not in rebuild_text

    # All three scripts accept --env / ENVIRONMENT selection.
    for text in (rebuild_text, dns_text, lambda_text):
        assert "--env" in text or "ENVIRONMENT" in text

    # DNS check must no longer hardcode dev hostnames in the python heredoc.
    assert 'by_name.get("dev.kinnoo.ai"' not in dns_text
    assert 'by_name.get("dev-api.kinnoo.ai"' not in dns_text
    assert "FRONTEND_SUBDOMAIN" in dns_text
    assert "API_SUBDOMAIN" in dns_text
    assert "BASE_DOMAIN" in dns_text

    # Lambda script must reference per-env tfvars and prod tfvars line emission.
    assert "environments/${ENVIRONMENT}/terraform.tfvars" in lambda_text
    assert "init -reconfigure" in lambda_text

    # Functional dry-run: rebuild script in dev mode without terraform should
    # still parse arguments and surface a clear error rather than silently
    # targeting prod.
    bash = shutil.which("bash")
    assert bash is not None

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for cmd in ("terraform", "docker", "aws"):
        stub = fake_bin / cmd
        stub.write_text("#!/usr/bin/env bash\nexit 0\n")
        stub.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        [bash, str(rebuild), "--env", "prod", "--dry-run"],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    # Script either succeeds in dry-run or fails with a clear prod-vs-dev
    # safety guard. It must NOT emit dev cluster names while ENVIRONMENT=prod.
    combined = result.stdout + result.stderr
    assert "kinnoo-dev-cluster" not in combined
    assert "kinnoo-dev-service" not in combined

    # Likewise dev mode must surface dev-derived defaults, not prod literals.
    result_dev = subprocess.run(
        [bash, str(rebuild), "--env", "dev", "--dry-run"],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    combined_dev = result_dev.stdout + result_dev.stderr
    assert "kinnoo-prod-" not in combined_dev
