"""kinnoo manifest validator.

Public API
----------
validate(manifest_path: str) -> tuple[bool, list[str]]
    Parse *manifest_path* as a kinnoo.yaml file and return a 2-tuple:

    * ``is_valid`` (bool) – True when the manifest passes all checks.
    * ``errors`` (list[str]) – Human-readable error messages; empty when
      is_valid is True.

Usage::

    is_valid, errors = validate("path/to/kinnoo.yaml")
    if not is_valid:
        for msg in errors:
            print(msg)
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    FIELD_TYPES,
    MCP_SERVER_PERMISSION_BOOL_FIELDS,
    MCP_SERVER_PERMISSION_KEYS,
    NAME_PATTERN,
    OPTIONAL_FIELD_TYPES,
    PERMISSIONS_BOOL_FIELDS,
    PERMISSIONS_KEYS,
    REQUIRED_FIELDS,
    SERVICE_TYPE_ALIASES,
    SEMVER_PATTERN,
    SUPPORTED_FILESYSTEM_SCOPES,
    SUPPORTED_HEALTH_CHECK_METHODS,
    SUPPORTED_INPUT_TYPES,
    SUPPORTED_NODE_PACKAGE_MANAGERS,
    SUPPORTED_OUTPUT_TYPES,
    SUPPORTED_RUNTIME_LANGUAGES,
    SUPPORTED_RUNTIME_TYPES,
    SUPPORTED_SERVICE_TYPES,
)

from .schema import normalize_manifest_defaults, normalize_type_field

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_types(manifest: dict) -> dict:
    """Normalize 'type' fields in inputs/outputs to always be lists."""
    m = dict(manifest)
    if 'inputs' in m and isinstance(m['inputs'], dict):
        normalize_type_field(m['inputs'])
    if 'outputs' in m and isinstance(m['outputs'], dict):
        normalize_type_field(m['outputs'])
    return m

def _get_nested(data: dict[str, Any], dotted_key: str) -> tuple[bool, Any]:
    """Retrieve a value from a nested dict using a dot-separated key path.

    Returns:
        (found, value) — found is False when any segment is missing.
    """
    parts = dotted_key.split(".")
    node: Any = data
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _collect_services_shape_errors(data: dict[str, Any]) -> list[str]:
    """Validate optional services structure and nested value types.

    Task146 scope is schema-shape support only. Required-field checks, enum
    validation, and duplicate-name validation are implemented in task147.
    """
    errors: list[str] = []
    found, services = _get_nested(data, "services")
    if not found:
        return errors

    if not isinstance(services, list):
        return errors

    seen_service_names: set[str] = set()
    duplicate_service_names: set[str] = set()

    for index, service in enumerate(services):
        if not isinstance(service, dict):
            actual = type(service).__name__
            errors.append(
                f"Field 'services[{index}]' must be of type dict, got {actual}."
            )
            continue

        if "name" not in service:
            errors.append(f"Missing required field: 'services[{index}].name'")
        if "type" not in service:
            errors.append(f"Missing required field: 'services[{index}].type'")

        service_name = service.get("name")
        if service_name is not None and not isinstance(service_name, str):
            actual = type(service_name).__name__
            errors.append(
                f"Field 'services[{index}].name' must be of type str, got {actual}."
            )
        elif isinstance(service_name, str):
            if service_name in seen_service_names:
                duplicate_service_names.add(service_name)
            else:
                seen_service_names.add(service_name)

        service_type = service.get("type")
        if service_type is not None and not isinstance(service_type, str):
            actual = type(service_type).__name__
            errors.append(
                f"Field 'services[{index}].type' must be of type str, got {actual}."
            )
        elif isinstance(service_type, str) and service_type not in SUPPORTED_SERVICE_TYPES:
            supported = ", ".join(f"'{value}'" for value in SUPPORTED_SERVICE_TYPES)
            errors.append(
                f"Field 'services[{index}].type' has unsupported value: '{service_type}'. "
                f"Allowed values: {supported}."
            )
        elif isinstance(service_type, str):
            # Canonicalization keeps semantic equivalence explicit for alias values.
            service_type = SERVICE_TYPE_ALIASES.get(service_type, service_type)

        health_check = service.get("health_check")
        if health_check is None:
            continue

        if not isinstance(health_check, dict):
            actual = type(health_check).__name__
            errors.append(
                f"Field 'services[{index}].health_check' must be of type dict, got {actual}."
            )
            continue

        if "method" not in health_check:
            errors.append(
                f"Missing required field: 'services[{index}].health_check.method' when health_check is declared."
            )
            continue

        method = health_check.get("method")
        if method is not None and not isinstance(method, str):
            actual = type(method).__name__
            errors.append(
                f"Field 'services[{index}].health_check.method' must be of type str, got {actual}."
            )
        elif isinstance(method, str) and method not in SUPPORTED_HEALTH_CHECK_METHODS:
            supported = ", ".join(
                f"'{value}'" for value in SUPPORTED_HEALTH_CHECK_METHODS
            )
            errors.append(
                f"Field 'services[{index}].health_check.method' has unsupported value: '{method}'. "
                f"Allowed values: {supported}."
            )

        url = health_check.get("url")
        if url is not None and not isinstance(url, str):
            actual = type(url).__name__
            errors.append(
                f"Field 'services[{index}].health_check.url' must be of type str, got {actual}."
            )

        process_name = health_check.get("process_name")
        if process_name is not None and not isinstance(process_name, str):
            actual = type(process_name).__name__
            errors.append(
                f"Field 'services[{index}].health_check.process_name' must be of type str, got {actual}."
            )

        port = health_check.get("port")
        if port is not None and (isinstance(port, bool) or not isinstance(port, int)):
            actual = type(port).__name__
            errors.append(
                f"Field 'services[{index}].health_check.port' must be of type int, got {actual}."
            )

        if method == "tcp" and "port" not in health_check:
            errors.append(
                f"Missing required field: 'services[{index}].health_check.port' when method is 'tcp'."
            )
        if method == "http" and "url" not in health_check:
            errors.append(
                f"Missing required field: 'services[{index}].health_check.url' when method is 'http'."
            )
        if method == "process" and "process_name" not in health_check:
            errors.append(
                f"Missing required field: 'services[{index}].health_check.process_name' when method is 'process'."
            )

    # Emit deterministic duplicate errors by sorting names.
    for duplicate_name in sorted(duplicate_service_names):
        errors.append(f"Duplicate service name not allowed: '{duplicate_name}'.")

    return errors


def _collect_mcp_server_permissions_errors(data: dict[str, Any]) -> list[str]:
    """Validate optional permissions payload for legacy and feature39 contracts."""
    errors: list[str] = []

    runtime_found, runtime_type = _get_nested(data, "runtime.type")
    if not runtime_found:
        return errors

    permissions_found, permissions = _get_nested(data, "permissions")
    if not permissions_found:
        return errors

    # Feature26 backward compatibility: non-mcp-server manifests historically
    # ignored non-dict permissions payloads.
    if runtime_type != "mcp-server" and not isinstance(permissions, dict):
        return errors

    if not isinstance(permissions, dict):
        actual = type(permissions).__name__
        errors.append(
            f"Field 'permissions' must be of type dict, got {actual}."
        )
        return errors

    feature39_keys = set(PERMISSIONS_KEYS)
    has_feature39_keys = any(key in feature39_keys for key in permissions)

    # Feature39 explicit permissions contract.
    if has_feature39_keys or runtime_type != "mcp-server":
        allowed_keys = feature39_keys
        allowed_keys_display = ", ".join(f"'{key}'" for key in PERMISSIONS_KEYS)

        for key in sorted(permissions.keys()):
            if key not in allowed_keys:
                errors.append(
                    f"Field 'permissions' contains unsupported key: '{key}'. "
                    f"Allowed keys: {allowed_keys_display}."
                )

        for field_name in PERMISSIONS_BOOL_FIELDS:
            if field_name not in permissions:
                continue
            value = permissions[field_name]
            if not isinstance(value, bool):
                actual = type(value).__name__
                errors.append(
                    f"Field 'permissions.{field_name}' must be of type bool, got {actual}."
                )

        if "filesystem_scope" in permissions:
            filesystem_scope = permissions["filesystem_scope"]
            if not isinstance(filesystem_scope, str):
                actual = type(filesystem_scope).__name__
                errors.append(
                    f"Field 'permissions.filesystem_scope' must be of type str, got {actual}."
                )
            elif filesystem_scope not in SUPPORTED_FILESYSTEM_SCOPES:
                supported_scopes = ", ".join(
                    f"'{scope}'" for scope in SUPPORTED_FILESYSTEM_SCOPES
                )
                errors.append(
                    "Field 'permissions.filesystem_scope' has unsupported value: "
                    f"'{filesystem_scope}'. Supported values: {supported_scopes}."
                )

        if "env_access" in permissions:
            env_access = permissions["env_access"]
            if not isinstance(env_access, list):
                actual = type(env_access).__name__
                errors.append(
                    f"Field 'permissions.env_access' must be of type list, got {actual}."
                )
            else:
                for index, env_var_name in enumerate(env_access):
                    if not isinstance(env_var_name, str):
                        actual = type(env_var_name).__name__
                        errors.append(
                            f"Field 'permissions.env_access[{index}]' must be of type str, got {actual}."
                        )
                        continue
                    if env_var_name.strip() == "":
                        errors.append(
                            f"Field 'permissions.env_access[{index}]' must be a non-empty string."
                        )

        return errors

    # Feature26 legacy mcp-server permissions schema contract.
    allowed_keys = set(MCP_SERVER_PERMISSION_KEYS)
    allowed_keys_display = ", ".join(f"'{key}'" for key in MCP_SERVER_PERMISSION_KEYS)

    for key in sorted(permissions.keys()):
        if key not in allowed_keys:
            errors.append(
                f"Field 'permissions' contains unsupported key: '{key}'. "
                f"Allowed keys: {allowed_keys_display}."
            )

    for field_name in MCP_SERVER_PERMISSION_BOOL_FIELDS:
        if field_name not in permissions:
            continue
        value = permissions[field_name]
        if not isinstance(value, bool):
            actual = type(value).__name__
            errors.append(
                f"Field 'permissions.{field_name}' must be of type bool, got {actual}."
            )

    if "allowed_paths" in permissions:
        allowed_paths = permissions["allowed_paths"]
        if not isinstance(allowed_paths, list):
            actual = type(allowed_paths).__name__
            errors.append(
                f"Field 'permissions.allowed_paths' must be of type list, got {actual}."
            )
        else:
            for index, value in enumerate(allowed_paths):
                if not isinstance(value, str):
                    actual = type(value).__name__
                    errors.append(
                        f"Field 'permissions.allowed_paths[{index}]' must be of type str, got {actual}."
                    )

    return errors


def _collect_io_type_errors(data: dict[str, Any]) -> list[str]:
    """Validate manifest input/output contract type values."""
    errors: list[str] = []

    io_field_specs: tuple[tuple[str, list[str]], ...] = (
        ("inputs.type", SUPPORTED_INPUT_TYPES),
        ("outputs.type", SUPPORTED_OUTPUT_TYPES),
    )

    for field_name, allowed_values in io_field_specs:
        found, value = _get_nested(data, field_name)
        if not found or not isinstance(value, list):
            continue

        for index, declared_type in enumerate(value):
            if not isinstance(declared_type, str):
                actual = type(declared_type).__name__
                errors.append(
                    f"Field '{field_name}[{index}]' must be of type str, got {actual}."
                )
                continue

            if declared_type not in allowed_values:
                allowed = ", ".join(f"'{item}'" for item in allowed_values)
                errors.append(
                    f"Field '{field_name}' has unsupported value: '{declared_type}'. "
                    f"Supported values: {allowed}."
                )

    return errors


def _is_safe_relative_manifest_path(path_value: str) -> bool:
    """Return True when a manifest path is relative and traversal-safe."""
    candidate = PurePosixPath(path_value)
    return not candidate.is_absolute() and ".." not in candidate.parts


def _is_safe_relative_pattern(pattern_value: str) -> bool:
    """Return True when an exclude pattern is relative and traversal-safe.

    Exclude values may contain glob syntax, so this helper validates only the
    safety properties we rely on for snapshot policy handling.
    """
    normalized = pattern_value.strip()
    if normalized == "":
        return False
    if normalized.startswith("/"):
        return False

    candidate = PurePosixPath(normalized)
    return ".." not in candidate.parts


def _collect_state_dirs_contract_errors(data: dict[str, Any]) -> list[str]:
    """Validate feature35 state_dirs contract shape and safety constraints."""
    errors: list[str] = []

    found, state_dirs_value = _get_nested(data, "state_dirs")
    if not found or not isinstance(state_dirs_value, list):
        return errors

    for index, declared_state_dir in enumerate(state_dirs_value):
        if isinstance(declared_state_dir, str):
            normalized_path = declared_state_dir.strip()
            if normalized_path == "":
                errors.append(
                    f"Field 'state_dirs[{index}]' must be a non-empty string."
                )
                continue
            if not _is_safe_relative_manifest_path(normalized_path):
                errors.append(
                    f"Field 'state_dirs[{index}]' must be a relative path without parent traversal segments."
                )
            continue

        if not isinstance(declared_state_dir, dict):
            actual = type(declared_state_dir).__name__
            errors.append(
                f"Field 'state_dirs[{index}]' must be of type str or dict, got {actual}."
            )
            continue

        if "path" not in declared_state_dir:
            errors.append(
                f"Missing required field: 'state_dirs[{index}].path'"
            )
            continue

        path_value = declared_state_dir.get("path")
        if not isinstance(path_value, str):
            actual = type(path_value).__name__
            errors.append(
                f"Field 'state_dirs[{index}].path' must be of type str, got {actual}."
            )
        else:
            normalized_path = path_value.strip()
            if normalized_path == "":
                errors.append(
                    f"Field 'state_dirs[{index}].path' must be a non-empty string."
                )
            elif not _is_safe_relative_manifest_path(normalized_path):
                errors.append(
                    f"Field 'state_dirs[{index}].path' must be a relative path without parent traversal segments."
                )

        if "exclude" in declared_state_dir:
            exclude_value = declared_state_dir["exclude"]
            if not isinstance(exclude_value, list):
                actual = type(exclude_value).__name__
                errors.append(
                    f"Field 'state_dirs[{index}].exclude' must be of type list, got {actual}."
                )
            else:
                for exclude_index, exclude_pattern in enumerate(exclude_value):
                    if not isinstance(exclude_pattern, str):
                        actual = type(exclude_pattern).__name__
                        errors.append(
                            f"Field 'state_dirs[{index}].exclude[{exclude_index}]' must be of type str, got {actual}."
                        )
                        continue
                    if not _is_safe_relative_pattern(exclude_pattern):
                        errors.append(
                            f"Field 'state_dirs[{index}].exclude[{exclude_index}]' must be a relative pattern without parent traversal segments."
                        )

    return errors


def _collect_openclaw_framework_errors(data: dict[str, Any]) -> list[str]:
    """Validate framework-specific rules for manifests declaring framework=openclaw."""
    errors: list[str] = []

    framework_found, framework_value = _get_nested(data, "framework")
    if not framework_found or not isinstance(framework_value, str):
        return errors
    if framework_value != "openclaw":
        return errors

    runtime_language_found, runtime_language_value = _get_nested(data, "runtime.language")
    if runtime_language_found and runtime_language_value != "nodejs":
        errors.append(
            "Field 'runtime.language' must be 'nodejs' when framework is 'openclaw'."
        )

    runtime_type_found, runtime_type_value = _get_nested(data, "runtime.type")
    if runtime_type_found and runtime_type_value != "daemon":
        errors.append(
            "Field 'runtime.type' must be 'daemon' when framework is 'openclaw'."
        )

    package_manager_found, package_manager_value = _get_nested(
        data, "runtime.package_manager"
    )
    if not package_manager_found:
        errors.append(
            "Field 'runtime.package_manager' is required when framework is 'openclaw'. "
            "Supported values: 'npm', 'pnpm'."
        )
    elif isinstance(package_manager_value, str) and package_manager_value not in SUPPORTED_NODE_PACKAGE_MANAGERS:
        # Keep framework-targeted guidance even when generic runtime validation also reports unsupported values.
        errors.append(
            "Field 'runtime.package_manager' must be one of 'npm', 'pnpm' when framework is 'openclaw'."
        )

    channels_found, channels_value = _get_nested(data, "channels")
    if channels_found and isinstance(channels_value, list) and "stdio" not in channels_value:
        errors.append(
            "Field 'channels' must include 'stdio' when framework is 'openclaw'."
        )

    return errors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _collect_validation_errors(data: dict[str, Any]) -> list[str]:
    """Collect schema/type/semantic validation errors for a manifest mapping."""
    errors: list[str] = []

    # Inject defaults for dependencies, inputs, outputs if missing
    data = normalize_manifest_defaults(data)
    # Normalize type fields in inputs/outputs to always be lists
    data = _normalize_types(data)

    # ------------------------------------------------------------------
    # 2. Required fields — presence check
    # ------------------------------------------------------------------
    for field in REQUIRED_FIELDS:
        found, _ = _get_nested(data, field)
        if not found:
            errors.append(f"Missing required field: '{field}'")

    # ------------------------------------------------------------------
    # 3. Type checks (only where the field is present)
    # ------------------------------------------------------------------
    for field, expected_type in FIELD_TYPES.items():
        found, value = _get_nested(data, field)
        if not found:
            continue  # already reported as missing above
        if not isinstance(value, expected_type):
            actual = type(value).__name__
            expected = expected_type.__name__
            errors.append(
                f"Field '{field}' must be of type {expected}, "
                f"got {actual}."
            )

    # ------------------------------------------------------------------
    # 4. Semantic validations (only when the field is present + correct type)
    # ------------------------------------------------------------------

    # 4a. version — must be valid semver
    version_found, version_value = _get_nested(data, "version")
    if version_found and isinstance(version_value, str):
        if not re.fullmatch(SEMVER_PATTERN, version_value):
            errors.append(
                f"Field 'version' has an invalid semver value: '{version_value}'. "
                "Expected format: MAJOR.MINOR.PATCH (e.g., '1.2.3')."
            )

    # 4b. name — must match package name pattern
    name_found, name_value = _get_nested(data, "name")
    if name_found and isinstance(name_value, str):
        if not re.fullmatch(NAME_PATTERN, name_value):
            errors.append(
                f"Field 'name' has an invalid value: '{name_value}'. "
                "Only lowercase alphanumeric characters, hyphens, and underscores are allowed, "
                "and it must start with a letter or digit."
            )

    # 4c. runtime.type — must be "one-shot"
    rt_found, rt_value = _get_nested(data, "runtime.type")
    if rt_found and isinstance(rt_value, str):
        if rt_value not in SUPPORTED_RUNTIME_TYPES:
            supported = ", ".join(f"'{v}'" for v in SUPPORTED_RUNTIME_TYPES)
            errors.append(
                f"Field 'runtime.type' has unsupported value: '{rt_value}'. "
                f"Only {supported} is supported in this version of kinnoo."
            )

    # 4d. runtime.language — must be a supported runtime language
    runtime_language_found, runtime_language_value = _get_nested(data, "runtime.language")
    if runtime_language_found and isinstance(runtime_language_value, str):
        if runtime_language_value not in SUPPORTED_RUNTIME_LANGUAGES:
            supported = ", ".join(f"'{value}'" for value in SUPPORTED_RUNTIME_LANGUAGES)
            errors.append(
                f"Field 'runtime.language' has unsupported value: '{runtime_language_value}'. "
                f"Supported values: {supported}."
            )

    runtime_package_manager_found, runtime_package_manager_value = _get_nested(
        data, "runtime.package_manager"
    )
    if runtime_package_manager_found and isinstance(runtime_package_manager_value, str):
        if runtime_package_manager_value not in SUPPORTED_NODE_PACKAGE_MANAGERS:
            supported = ", ".join(
                f"'{value}'" for value in SUPPORTED_NODE_PACKAGE_MANAGERS
            )
            errors.append(
                f"Field 'runtime.package_manager' has unsupported value: '{runtime_package_manager_value}'. "
                f"Supported values: {supported}."
            )

    # 4e. Optional V2 fields (feature9).
    # Validate optional metadata when present while preserving V1 compatibility.
    for optional_field, expected_type in OPTIONAL_FIELD_TYPES.items():
        found, value = _get_nested(data, optional_field)
        if not found:
            continue

        if not isinstance(value, expected_type):
            actual = type(value).__name__
            if isinstance(expected_type, tuple):
                expected = " or ".join(t.__name__ for t in expected_type)
            else:
                expected = expected_type.__name__
            errors.append(
                f"Field '{optional_field}' must be of type {expected}, "
                f"got {actual}."
            )
            continue

        if optional_field == "env_vars":
            for index, env_var in enumerate(value):
                if not isinstance(env_var, str):
                    actual = type(env_var).__name__
                    errors.append(
                        f"Field 'env_vars[{index}]' must be of type str, got {actual}."
                    )
                    continue
                if env_var.strip() == "":
                    errors.append(
                        f"Field 'env_vars[{index}]' must be a non-empty string."
                    )

        if optional_field == "model" and value.strip() == "":
            errors.append("Field 'model' must be a non-empty string.")

        if optional_field == "assets.max_bundle_size_mb" and isinstance(value, bool):
            errors.append("Field 'assets.max_bundle_size_mb' must be of type int or float, got bool.")

        if optional_field == "assets.paths":
            for index, asset_path in enumerate(value):
                if not isinstance(asset_path, str):
                    actual = type(asset_path).__name__
                    errors.append(
                        f"Field 'assets.paths[{index}]' must be of type str, got {actual}."
                    )
                    continue
                if asset_path.strip() == "":
                    errors.append(
                        f"Field 'assets.paths[{index}]' must be a non-empty string."
                    )

        if optional_field == "channels":
            for index, channel_name in enumerate(value):
                if not isinstance(channel_name, str):
                    actual = type(channel_name).__name__
                    errors.append(
                        f"Field 'channels[{index}]' must be of type str, got {actual}."
                    )
                    continue
                if channel_name.strip() == "":
                    errors.append(
                        f"Field 'channels[{index}]' must be a non-empty string."
                    )

        if optional_field == "skills":
            for index, declared_path in enumerate(value):
                if not isinstance(declared_path, str):
                    actual = type(declared_path).__name__
                    errors.append(
                        f"Field '{optional_field}[{index}]' must be of type str, got {actual}."
                    )
                    continue

                normalized_path = declared_path.strip()
                if normalized_path == "":
                    errors.append(
                        f"Field '{optional_field}[{index}]' must be a non-empty string."
                    )
                    continue

                if not _is_safe_relative_manifest_path(normalized_path):
                    errors.append(
                        f"Field '{optional_field}[{index}]' must be a relative path without parent traversal segments."
                    )

    errors.extend(_collect_services_shape_errors(data))
    errors.extend(_collect_mcp_server_permissions_errors(data))
    errors.extend(_collect_io_type_errors(data))
    errors.extend(_collect_state_dirs_contract_errors(data))
    errors.extend(_collect_openclaw_framework_errors(data))

    return errors


def validate_manifest_data(manifest_data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate an in-memory kinnoo manifest mapping.

    Parameters
    ----------
    manifest_data:
        Parsed manifest object expected to be a YAML top-level mapping.

    Returns
    -------
    tuple[bool, list[str]]
        ``(is_valid, errors)`` where *errors* is empty when valid.
    """
    if not isinstance(manifest_data, dict):
        return False, ["Manifest must be a YAML mapping (dict) at the top level."]

    errors = _collect_validation_errors(manifest_data)
    return len(errors) == 0, errors


def validate(manifest_path: str) -> tuple[bool, list[str]]:
    """Validate a kinnoo.yaml manifest file.

    Parameters
    ----------
    manifest_path:
        Filesystem path to the manifest file (``kinnoo.yaml``).

    Returns
    -------
    tuple[bool, list[str]]
        ``(is_valid, errors)`` where *errors* is an empty list when
        *is_valid* is ``True``.
    """
    path = Path(manifest_path)

    # ------------------------------------------------------------------
    # 1. File existence and YAML parse
    # ------------------------------------------------------------------
    if not path.exists():
        return False, [f"Manifest file not found: {manifest_path}"]

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        return False, [f"YAML parse error: {exc}"]

    if not isinstance(data, dict):
        return False, ["Manifest must be a YAML mapping (dict) at the top level."]

    return validate_manifest_data(data)
