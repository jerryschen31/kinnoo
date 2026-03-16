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
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    FIELD_TYPES,
    NAME_PATTERN,
    OPTIONAL_FIELD_TYPES,
    REQUIRED_FIELDS,
    SEMVER_PATTERN,
    SUPPORTED_RUNTIME_TYPES,
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

    for index, service in enumerate(services):
        if not isinstance(service, dict):
            actual = type(service).__name__
            errors.append(
                f"Field 'services[{index}]' must be of type dict, got {actual}."
            )
            continue

        service_name = service.get("name")
        if service_name is not None and not isinstance(service_name, str):
            actual = type(service_name).__name__
            errors.append(
                f"Field 'services[{index}].name' must be of type str, got {actual}."
            )

        service_type = service.get("type")
        if service_type is not None and not isinstance(service_type, str):
            actual = type(service_type).__name__
            errors.append(
                f"Field 'services[{index}].type' must be of type str, got {actual}."
            )

        health_check = service.get("health_check")
        if health_check is None:
            continue

        if not isinstance(health_check, dict):
            actual = type(health_check).__name__
            errors.append(
                f"Field 'services[{index}].health_check' must be of type dict, got {actual}."
            )
            continue

        method = health_check.get("method")
        if method is not None and not isinstance(method, str):
            actual = type(method).__name__
            errors.append(
                f"Field 'services[{index}].health_check.method' must be of type str, got {actual}."
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

    # 4d. Optional V2 fields (feature9).
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

    errors.extend(_collect_services_shape_errors(data))

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
