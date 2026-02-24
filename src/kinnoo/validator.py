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
    REQUIRED_FIELDS,
    SEMVER_PATTERN,
    SUPPORTED_RUNTIME_TYPES,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
    errors: list[str] = []
    path = Path(manifest_path)

    # ------------------------------------------------------------------
    # 1. File existence and YAML parse
    # ------------------------------------------------------------------
    if not path.exists():
        errors.append(f"Manifest file not found: {manifest_path}")
        return False, errors

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        errors.append(f"YAML parse error: {exc}")
        return False, errors

    if not isinstance(data, dict):
        errors.append("Manifest must be a YAML mapping (dict) at the top level.")
        return False, errors

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

    # ------------------------------------------------------------------
    # 5. Optional field: framework — accepted if present as a string,
    #    silently ignored if absent.  Already handled by only validating
    #    required fields above; no action needed here.
    # ------------------------------------------------------------------

    is_valid = len(errors) == 0
    return is_valid, errors
