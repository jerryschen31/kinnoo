from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_feature106_group1() -> None:
    module_main = _read("iac/modules/cloudflare/main.tf")
    module_vars = _read("iac/modules/cloudflare/variables.tf")

    assert 'resource "cloudflare_record" "dev_pages"' in module_main
    assert 'resource "cloudflare_record" "dev_api"' in module_main
    assert 'name    = local.dev_host' in module_main
    assert 'name    = local.dev_api_host' in module_main
    assert 'type    = "CNAME"' in module_main
    assert 'value   = var.pages_target' in module_main
    assert 'value   = var.alb_dns_name' in module_main
    assert 'proxied = true' in module_main

    assert 'variable "zone_id"' in module_vars
    assert 'variable "alb_dns_name"' in module_vars


def test_feature106_group2() -> None:
    module_main = _read("iac/modules/cloudflare/main.tf")
    module_vars = _read("iac/modules/cloudflare/variables.tf")
    providers_tf = _read("iac/providers.tf")

    assert "acm_validation_records" in module_vars
    assert "for_each" in module_main
    assert 'resource "cloudflare_dns_record" "acm_validation"' in module_main
    assert "CLOUDFLARE_API_TOKEN" in providers_tf
    assert 'terraform {' in _read("iac/versions.tf")
