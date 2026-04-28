from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]

pytestmark = [pytest.mark.regression_integration, pytest.mark.integration, pytest.mark.security_checks]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"Expected to find '{needle}' in configuration"


def test_feature121_test741_prod_dev_dns_isolation() -> None:
    main_tf = _read("iac/main.tf")
    cloudflare_tf = _read("iac/modules/cloudflare/main.tf")
    cloudflare_vars_tf = _read("iac/modules/cloudflare/variables.tf")
    prod_tfvars = _read("iac/environments/prod/terraform.tfvars")

    # Root IaC must derive API domain from environment-specific tfvars, not hardcode dev.
    _assert_contains(main_tf, 'api_domain            = local.api_domain')
    _assert_contains(main_tf, 'api_domain = "${var.api_record_name}.${var.base_domain}"')
    assert 'api_domain            = "dev-api.kinnoo.ai"' not in main_tf

    # Cloudflare module must use generic API/frontend record resources and variables.
    _assert_contains(cloudflare_tf, 'resource "cloudflare_record" "frontend"')
    _assert_contains(cloudflare_tf, 'resource "cloudflare_record" "api"')
    _assert_contains(cloudflare_tf, 'name    = local.api_host')
    _assert_contains(cloudflare_tf, 'name    = local.frontend_host')
    assert 'resource "cloudflare_record" "dev_pages"' not in cloudflare_tf
    assert 'resource "cloudflare_record" "dev_api"' not in cloudflare_tf
    assert 'local.dev_host' not in cloudflare_tf
    assert 'local.dev_api_host' not in cloudflare_tf
    _assert_contains(cloudflare_tf, "from = cloudflare_record.dev_api")
    _assert_contains(cloudflare_tf, "to   = cloudflare_record.api")
    _assert_contains(cloudflare_vars_tf, 'variable "api_record_name"')
    _assert_contains(cloudflare_vars_tf, 'variable "frontend_record_name"')
    _assert_contains(cloudflare_vars_tf, 'variable "manage_frontend_record"')

    # Prod tfvars must explicitly use prod API and frontend hostnames.
    _assert_contains(prod_tfvars, 'api_record_name     = "api"')
    _assert_contains(prod_tfvars, 'frontend_record_name = "@"')


def test_feature121_test741_dev_dns_contract_preserved() -> None:
    main_tf = _read("iac/main.tf")
    dev_tfvars = _read("iac/environments/dev/terraform.tfvars")

    # Existing dev controls remain wired to Cloudflare frontend management knobs.
    _assert_contains(main_tf, 'frontend_record_type  = var.dev_record_type')
    _assert_contains(main_tf, 'frontend_record_content = var.dev_record_content')
    _assert_contains(main_tf, 'manage_frontend_record = var.manage_dev_record')

    # Dev environment remains explicitly scoped to dev/dev-api hostnames.
    _assert_contains(dev_tfvars, 'api_record_name     = "dev-api"')
    _assert_contains(dev_tfvars, 'frontend_record_name = "dev"')
