from __future__ import annotations
# ---------------------------------------------------------------------------
# Manifest normalization: inject defaults for missing fields
# ---------------------------------------------------------------------------
def normalize_manifest_defaults(manifest: dict) -> dict:
    """Inject defaults for dependencies, inputs, outputs if missing."""
    m = dict(manifest)  # shallow copy
    if "dependencies" not in m:
        m["dependencies"] = []
    if "inputs" not in m:
        m["inputs"] = {"type": "string"}
    elif "type" not in m["inputs"]:
        m["inputs"]["type"] = "string"
    if "outputs" not in m:
        m["outputs"] = {"type": "string"}
    elif "type" not in m["outputs"]:
        m["outputs"]["type"] = "string"
    return m

# ---------------------------------------------------------------------------
# Normalize 'type' field in inputs/outputs to always be a list
# ---------------------------------------------------------------------------
def normalize_type_field(io_dict: dict) -> None:
    """Normalize the 'type' field in an IO dict to always be a list."""
    t = io_dict.get('type')
    if isinstance(t, str):
        io_dict['type'] = [t]
    elif isinstance(t, list):
        io_dict['type'] = t
    # else: leave as-is (should not happen if defaults are injected)


def normalize_env_vars(env_vars: object) -> list[str]:
    """Normalize env_vars to a deterministic list of unique non-empty names.

    This helper is runtime-oriented and intentionally defensive. Validator-level
    type checks still own strict schema enforcement.
    """
    if not isinstance(env_vars, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for value in env_vars:
        if not isinstance(value, str):
            continue
        name = value.strip()
        if not name or name in seen:
            continue
        normalized.append(name)
        seen.add(name)
    return normalized
"""Schema constants for kinnoo.yaml manifest validation.

Required fields and their expected Python types.  Nested fields use dot
notation (e.g., ``runtime.language``).
"""

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
    "inputs.type": list,
    "outputs.type": list,
}

# The only supported runtime type in this version of kinnoo.
SUPPORTED_RUNTIME_TYPES: list[str] = ["one-shot"]

# Optional V2 manifest metadata fields (feature9).
# These are intentionally optional and should not be included in REQUIRED_FIELDS.
OPTIONAL_FIELDS: list[str] = [
    "description",
    "author",
    "license",
    "env_vars",
]

# Expected types for optional V2 fields when present.
# Enforced in a later validation phase to keep feature rollout scoped by task.
OPTIONAL_FIELD_TYPES: dict[str, type] = {
    "description": str,
    "author": str,
    "license": str,
    "env_vars": list,
}

# Regex for a valid semver string: MAJOR.MINOR.PATCH with optional pre-release
# and build metadata (https://semver.org).
SEMVER_PATTERN: str = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

# Valid package name: lowercase alphanumeric, starting with a letter or digit,
# hyphens and underscores allowed between characters.
NAME_PATTERN: str = r"^[a-z0-9][a-z0-9-_]*$"
