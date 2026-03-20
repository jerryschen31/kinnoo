"""Configuration helpers for Kinnoo CLI and registry integrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import os


DEFAULT_CONFIG_PATH = Path.home() / ".kinnoo" / "config.yaml"


@dataclass(frozen=True)
class RegistryConfig:
    """Resolved registry settings with env-var precedence over config file."""

    registry_url: str | None
    registry_token: str | None
    tenant_slug: str | None


def load_registry_config(config_path: Path | None = None) -> RegistryConfig:
    """Load registry config from file and apply environment overrides.

    Precedence order:
    1) Environment variables
    2) YAML config file (if present)
    3) None for missing keys
    """

    resolved_path = (config_path or DEFAULT_CONFIG_PATH).expanduser()
    file_values = _read_registry_values_from_file(resolved_path)

    return RegistryConfig(
        registry_url=_coalesce_env_or_file(
            env_var_name="KINNOO_REGISTRY_URL",
            file_values=file_values,
            file_key="registry_url",
        ),
        registry_token=_coalesce_env_or_file(
            env_var_name="KINNOO_REGISTRY_TOKEN",
            file_values=file_values,
            file_key="registry_token",
        ),
        tenant_slug=_coalesce_env_or_file(
            env_var_name="KINNOO_TENANT_SLUG",
            file_values=file_values,
            file_key="tenant_slug",
        ),
    )


def _read_registry_values_from_file(config_path: Path) -> dict[str, str]:
    if not config_path.exists() or not config_path.is_file():
        return {}

    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    loaded = _parse_simple_yaml_object(raw_text)
    if not isinstance(loaded, dict):
        return {}

    normalized: dict[str, str] = {}
    for key in ("registry_url", "registry_token", "tenant_slug"):
        value = loaded.get(key)
        if isinstance(value, str) and value.strip():
            normalized[key] = value.strip()

    return normalized


def _parse_simple_yaml_object(text: str) -> dict[str, Any]:
    """Parse a minimal top-level YAML object for key:value scalar pairs.

    This parser intentionally supports only the subset needed for task231
    (`registry_url`, `registry_token`, `tenant_slug`) to avoid introducing
    a hard dependency for this config-loading path.
    """

    parsed: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue

        key_part, value_part = line.split(":", 1)
        key = key_part.strip()
        value = value_part.strip()
        if not key:
            continue

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        parsed[key] = value

    return parsed


def _coalesce_env_or_file(
    *,
    env_var_name: str,
    file_values: dict[str, str],
    file_key: str,
) -> str | None:
    env_value = os.environ.get(env_var_name)
    if isinstance(env_value, str) and env_value.strip():
        return env_value.strip()

    return file_values.get(file_key)
