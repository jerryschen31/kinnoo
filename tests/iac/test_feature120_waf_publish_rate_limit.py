from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_feature120_test750_waf_publish_ip_rate_limit_contract() -> None:
    terraform = _read("iac/modules/alb/main.tf")

    assert 'resource "aws_wafv2_web_acl" "alb"' in terraform
    assert 'resource "aws_wafv2_web_acl_association" "alb"' in terraform
    assert "rate_based_statement" in terraform
    assert "aggregate_key_type = \"IP\"" in terraform
    assert "limit              = 100" in terraform
    assert "search_string         = \"/api/publish\"" in terraform
