"""Tests for task520 / test743: production runtime config hardening.

The production CORS contract must reject implicit dev-domain fallbacks. In
production mode `CORS_ORIGINS` must be set explicitly; in dev mode the
permissive `*` fallback is preserved.
"""
from __future__ import annotations

import pytest

from server.config import ServerConfig


def _baseline_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset env vars that influence ServerConfig.from_env so tests are hermetic."""
    for name in [
        "KINNOO_ENV",
        "CORS_ORIGINS",
        "REGISTRY_STORAGE_BACKEND",
        "REGISTRY_LOCAL_STORAGE_ROOT",
        "REGISTRY_S3_BUCKET",
        "REGISTRY_S3_REGION",
        "REGISTRY_METADATA_BACKEND",
    ]:
        monkeypatch.delenv(name, raising=False)


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.security_checks
def test_feature121_test743_prod_requires_explicit_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production mode without CORS_ORIGINS must fail fast (no dev fallback)."""
    _baseline_env(monkeypatch)
    monkeypatch.setenv("KINNOO_ENV", "production")

    with pytest.raises(ValueError) as error:
        ServerConfig.from_env()

    message = str(error.value)
    assert "CORS_ORIGINS" in message
    assert "production" in message


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.security_checks
def test_feature121_test743_prod_accepts_explicit_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production mode with explicit prod origins must succeed."""
    _baseline_env(monkeypatch)
    monkeypatch.setenv("KINNOO_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "https://www.kinnoo.ai,https://api.kinnoo.ai")

    cfg = ServerConfig.from_env()

    assert cfg.kinnoo_env == "production"
    assert cfg.cors_origins == ("https://www.kinnoo.ai", "https://api.kinnoo.ai")


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.security_checks
def test_feature121_test743_prod_does_not_silently_fall_back_to_dev_domains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production mode must never pick up dev.kinnoo.ai/dev-api.kinnoo.ai by default."""
    _baseline_env(monkeypatch)
    monkeypatch.setenv("KINNOO_ENV", "production")

    with pytest.raises(ValueError):
        ServerConfig.from_env()

    # Even when only whitespace is supplied, behavior must be the strict error.
    monkeypatch.setenv("CORS_ORIGINS", "   ,   ")
    with pytest.raises(ValueError):
        ServerConfig.from_env()


@pytest.mark.regression_integration
@pytest.mark.server_api
def test_feature121_test743_dev_keeps_permissive_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dev mode without CORS_ORIGINS keeps the existing permissive fallback."""
    _baseline_env(monkeypatch)
    monkeypatch.setenv("KINNOO_ENV", "dev")

    cfg = ServerConfig.from_env()

    assert cfg.kinnoo_env == "dev"
    assert cfg.cors_origins == ("*",)
