"""Schema constants for kinnoo.yaml manifest validation.

Required fields and their expected Python types.  Nested fields use dot
notation (e.g., ``runtime.language``).
"""

from __future__ import annotations

# Fields that MUST be present in every kinnoo.yaml manifest.
# Dot-separated paths represent nested dicts (e.g. "runtime.language"
# means manifest["runtime"]["language"]).
REQUIRED_FIELDS: list[str] = [
    "name",
    "version",
    "entrypoint",
    "runtime.language",
    "runtime.version",
    "runtime.type",
    "dependencies",
    "inputs.type",
    "outputs.type",
]

# Expected Python type for each required field.
# Values are the actual type objects used in isinstance() checks.
FIELD_TYPES: dict[str, type] = {
    "name": str,
    "version": str,
    "entrypoint": str,
    "runtime.language": str,
    "runtime.version": str,
    "runtime.type": str,
    "dependencies": list,
    "inputs.type": str,
    "outputs.type": str,
}

# The only supported runtime type in this version of kinnoo.
SUPPORTED_RUNTIME_TYPES: list[str] = ["one-shot"]

# Regex for a valid semver string: MAJOR.MINOR.PATCH with optional pre-release
# and build metadata (https://semver.org).
SEMVER_PATTERN: str = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

# Valid package name: lowercase alphanumeric, starting with a letter or digit,
# hyphens allowed between characters.
NAME_PATTERN: str = r"^[a-z0-9][a-z0-9-]*$"
