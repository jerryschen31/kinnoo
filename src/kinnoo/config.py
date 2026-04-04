"""Configuration helpers for Kinnoo CLI and registry integrations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import os


DEFAULT_CONFIG_PATH = Path.home() / ".kinnoo" / "config.yaml"
DEFAULT_LOCKFILE_PATH = Path.home() / ".kinnoo" / "kinnoo-lock.yaml"
CLAW_HUB_TENANT_SLUG = "clawhub"


@dataclass(frozen=True)
class RegistryConfig:
    """Resolved registry settings with env-var precedence over config file."""

    registry_url: str | None
    registry_token: str | None
    tenant_slug: str | None


@dataclass(frozen=True)
class PublishBehaviorConfig:
    """Project-level publish behavior flags loaded from kinnoo-config.txt."""

    publish_to_authenticated_registry: bool


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


def load_publish_behavior_config(start_dir: Path | None = None) -> PublishBehaviorConfig:
    """Load project-level publish behavior flags.

    Expected file location: nearest ``kinnoo-config.txt`` from ``start_dir`` (or CWD)
    walking up to filesystem root.
    """

    config_path = _find_project_config_file(start_dir=start_dir)
    if config_path is None:
        return PublishBehaviorConfig(publish_to_authenticated_registry=False)

    file_values = _read_publish_values_from_file(config_path)
    return PublishBehaviorConfig(
        publish_to_authenticated_registry=_parse_bool_value(
            file_values.get("publish_to_authenticated_registry"),
            default=False,
        )
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


def _read_publish_values_from_file(config_path: Path) -> dict[str, str]:
    if not config_path.exists() or not config_path.is_file():
        return {}

    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    parsed: dict[str, str] = {}
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            key_part, value_part = line.split("=", 1)
        elif ":" in line:
            key_part, value_part = line.split(":", 1)
        else:
            continue

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


def _find_project_config_file(start_dir: Path | None = None) -> Path | None:
    current = (start_dir or Path.cwd()).expanduser().resolve()

    for candidate in (current, *current.parents):
        config_path = candidate / "kinnoo-config.txt"
        if config_path.exists() and config_path.is_file():
            return config_path

    return None


def _parse_bool_value(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


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


def resolve_lockfile_path(start_dir: Path | None = None) -> Path:
    """Resolve lockfile path with env override and project/global defaults."""

    env_override = (os.environ.get("KINNOO_LOCKFILE_PATH") or "").strip()
    if env_override:
        return Path(env_override).expanduser()

    resolved_start = (start_dir or Path.cwd()).expanduser().resolve()
    if (resolved_start / "kinnoo.yaml").exists():
        return resolved_start / "kinnoo-lock.yaml"

    return DEFAULT_LOCKFILE_PATH


def save_registry_auth_state(
    *,
    registry_url: str,
    registry_token: str,
    tenant_slug: str,
    config_path: Path | None = None,
) -> None:
    """Persist registry auth state in config file with secure file permissions."""

    resolved_path = (config_path or DEFAULT_CONFIG_PATH).expanduser()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    existing_values: dict[str, Any] = {}
    if resolved_path.exists() and resolved_path.is_file():
        try:
            existing_values = _parse_simple_yaml_object(resolved_path.read_text(encoding="utf-8"))
        except OSError:
            existing_values = {}

    existing_values["registry_url"] = registry_url.strip()
    existing_values["registry_token"] = registry_token.strip()
    existing_values["tenant_slug"] = tenant_slug.strip()

    payload = _dump_simple_yaml_object(existing_values)
    resolved_path.write_text(payload, encoding="utf-8")

    try:
        resolved_path.chmod(0o600)
    except OSError:
        # Best-effort hardening; keep behavior cross-platform safe.
        pass


def clear_registry_auth_state(config_path: Path | None = None) -> bool:
    """Clear persisted registry auth keys and return True if any key was removed."""

    resolved_path = (config_path or DEFAULT_CONFIG_PATH).expanduser()
    if not resolved_path.exists() or not resolved_path.is_file():
        return False

    try:
        existing_values = _parse_simple_yaml_object(resolved_path.read_text(encoding="utf-8"))
    except OSError:
        return False

    removed = False
    for key in ("registry_url", "registry_token", "tenant_slug"):
        if key in existing_values:
            existing_values.pop(key, None)
            removed = True

    if not removed:
        return False

    if existing_values:
        resolved_path.write_text(_dump_simple_yaml_object(existing_values), encoding="utf-8")
    else:
        resolved_path.unlink(missing_ok=True)

    return True


def _dump_simple_yaml_object(values: dict[str, Any]) -> str:
    ordered_keys = ["registry_url", "registry_token", "tenant_slug"]
    trailing_keys = sorted(k for k in values if k not in ordered_keys)
    final_order = [k for k in ordered_keys if k in values] + trailing_keys

    lines: list[str] = []
    for key in final_order:
        value = values.get(key)
        if value is None:
            continue
        text = str(value)
        escaped = text.replace("'", "''")
        lines.append(f"{key}: '{escaped}'")
    return "\n".join(lines) + ("\n" if lines else "")
