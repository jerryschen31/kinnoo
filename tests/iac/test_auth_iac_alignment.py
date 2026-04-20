from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_task496_dual_app_secret_wiring() -> None:
    secrets_main = _read("iac/modules/secrets/main.tf")
    ecs_main = _read("iac/modules/ecs-fargate/main.tf")

    required_secret_keys = [
        "AUTH_WEB_CLIENT_ID",
        "AUTH_WEB_CLIENT_SECRET",
        "AUTH_CLI_CLIENT_ID",
        "AUTH_ISSUER_URL",
        "AUTH_AUDIENCE",
        "AUTH_WEB_REDIRECT_URI",
        "AUTH_LOGOUT_REDIRECT_URI",
        "AUTH_JWKS_ENDPOINT_URL",
        "AUTH_TOKEN_ENDPOINT",
        "AUTH_AUTHORIZATION_ENDPOINT",
        "AUTH_LOGOUT_ENDPOINT",
        "AUTH_USERINFO_ENDPOINT",
        "AUTH_REVOCATION_ENDPOINT",
        "KINDE_WEB_CLIENT_ID",
        "KINDE_WEB_CLIENT_SECRET",
        "KINDE_CLI_CLIENT_ID",
        "KINDE_ISSUER_URL",
        "KINDE_AUDIENCE",
        "KINDE_WEB_REDIRECT_URI",
        "KINDE_LOGOUT_REDIRECT_URI",
    ]

    for key in required_secret_keys:
        assert key in secrets_main, f"Missing canonical auth secret key in secrets module: {key}"
        assert key in ecs_main, f"Missing canonical auth secret key in ECS secret wiring: {key}"

    assert 'output "secret_arns"' in secrets_main
    assert 'data "aws_secretsmanager_secret" "kinde_web_client_id"' in secrets_main
    assert 'data "aws_secretsmanager_secret" "kinde_web_client_secret"' in secrets_main
    assert 'data "aws_secretsmanager_secret" "kinde_cli_client_id"' in secrets_main

    # Step5 requires auth-related container definition updates to be applied.
    assert "ignore_changes = [container_definitions, volume]" not in ecs_main
    assert "ignore_changes = [task_definition]" not in ecs_main


def test_task496_dev_tfvars_and_cloudflare_runtime_contract() -> None:
    dev_tfvars = _read("iac/environments/dev/terraform.tfvars")
    cloudflare_main = _read("iac/modules/cloudflare/main.tf")
    setup_notes = _read("notes/kinde-auth-setup-dev.md")

    assert 'auth_provider       = "oidc_kinde"' in dev_tfvars

    # Current IaC model only manages Cloudflare DNS records.
    assert 'resource "cloudflare_record" "dev_pages"' in cloudflare_main
    assert 'resource "cloudflare_record" "dev_api"' in cloudflare_main
    assert 'resource "cloudflare_record" "acm_validation"' in cloudflare_main

    # Manual runtime fallback must be explicit while runtime vars are outside current IaC scope.
    assert "Cloudflare Worker runtime variables are not managed by current Terraform resources" in setup_notes
    assert "Manual Cloudflare runtime fallback" in setup_notes
    assert "BACKEND_URL" in setup_notes
    assert "https://dev-api.kinnoo.ai" in setup_notes
