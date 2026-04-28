"""task518 / test741: prod-domain and DNS isolation contract.

Static parsing tests that assert iac/main.tf and the cloudflare module no
longer hardcode dev domain literals, and that dev/prod tfvars surface
distinct frontend/api subdomain values.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IAC = ROOT / "iac"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _parse_tfvars(rel: str) -> dict[str, str]:
    """Very small tfvars parser: key = value (string/number/bool/list)."""
    text = _read(rel)
    out: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        out[key.strip()] = value.strip().strip('"')
    return out


@pytest.mark.regression_integration
@pytest.mark.security_checks
def test_feature121_test741_prod_dev_dns_isolation() -> None:
    main_tf = _read("iac/main.tf")
    cf_main = _read("iac/modules/cloudflare/main.tf")
    cf_vars = _read("iac/modules/cloudflare/variables.tf")

    # Root must not bind the ALB ACM cert to a dev-only literal.
    assert 'api_domain            = "dev-api.kinnoo.ai"' not in main_tf
    assert "local.api_fqdn" in main_tf

    # Cloudflare module must no longer contain dev-only host literals.
    assert 'dev_host' not in cf_main
    assert 'dev_api_host' not in cf_main
    assert "var.frontend_subdomain" in cf_main
    assert "var.api_subdomain" in cf_main

    # Module variables must expose the neutral inputs used by the root module.
    for required_var in (
        "frontend_subdomain",
        "api_subdomain",
        "frontend_record_type",
        "frontend_record_content",
        "manage_frontend_record",
    ):
        assert re.search(rf'variable\s+"{required_var}"', cf_vars), required_var

    # Both env tfvars must declare distinct frontend/api subdomains so a single
    # apply cannot mutate the other environment's records.
    dev = _parse_tfvars("iac/environments/dev/terraform.tfvars")
    prod = _parse_tfvars("iac/environments/prod/terraform.tfvars")

    for key in ("frontend_subdomain", "api_subdomain"):
        assert key in dev, f"dev tfvars missing {key}"
        assert key in prod, f"prod tfvars missing {key}"
        assert dev[key] != prod[key], f"dev/prod must differ on {key}"

    # Specifically the prod api subdomain must not be the dev api subdomain.
    assert prod["api_subdomain"] != "dev-api"
    assert prod["frontend_subdomain"] != "dev"
