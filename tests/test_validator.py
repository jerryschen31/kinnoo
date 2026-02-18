"""Unit tests for kinnoo manifest validator (feature1, test0–test6).

Each test corresponds to specific acceptance criteria as declared in TESTS.txt.

Automation paths:
    test0  → test_valid_manifest_passes           (feature1:AC1)
    test1  → test_missing_required_field          (feature1:AC2)
    test2  → test_invalid_field_type              (feature1:AC3)
    test3  → test_invalid_semver_format           (feature1:AC4)
    test4  → test_validator_return_type           (feature1:AC5)
    test5  → test_framework_optional              (feature1:AC6)
    test6  → test_invalid_runtime_type            (feature1:AC7)
"""

from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path

import pytest
import yaml

# Allow importing from src/kinnoo without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kinnoo.validator import validate  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_MANIFEST: dict = {
    "name": "my-agent",
    "version": "0.1.0",
    "entrypoint": "run.py",
    "runtime": {
        "language": "python",
        "version": ">=3.10",
        "type": "one-shot",
    },
    "dependencies": ["openai", "requests"],
    "inputs": {"type": "text"},
    "outputs": {"type": "text"},
}


def _write_manifest(data: dict, tmp_path: Path) -> Path:
    """Write *data* as YAML to a temp file and return its path."""
    p = tmp_path / "kinnoo.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# test0 — valid manifest passes (feature1:AC1)
# ---------------------------------------------------------------------------

def test_valid_manifest_passes(tmp_path: Path) -> None:
    """A fully valid kinnoo.yaml returns (True, [])."""
    p = _write_manifest(_VALID_MANIFEST, tmp_path)
    is_valid, errors = validate(str(p))
    assert is_valid is True, f"Expected valid manifest to pass; errors: {errors}"
    assert errors == [], f"Expected empty error list; got: {errors}"


# ---------------------------------------------------------------------------
# test1 — missing required field produces specific error (feature1:AC2)
# ---------------------------------------------------------------------------

def test_missing_required_field(tmp_path: Path) -> None:
    """Omitting 'entrypoint' produces an error that names the field."""
    data = dict(_VALID_MANIFEST)
    del data["entrypoint"]
    p = _write_manifest(data, tmp_path)
    is_valid, errors = validate(str(p))
    assert is_valid is False, "Expected validation to fail for missing field"
    assert any("entrypoint" in msg for msg in errors), (
        f"Expected error mentioning 'entrypoint'; got: {errors}"
    )


def test_missing_required_field_all(tmp_path: Path) -> None:
    """Each required field individually triggers a named error when omitted."""
    required_top_level = [
        "name", "version", "entrypoint", "dependencies",
    ]
    nested_required = {
        "runtime": ["language", "version", "type"],
        "inputs": ["type"],
        "outputs": ["type"],
    }

    for field in required_top_level:
        data = {
            k: v
            for k, v in _VALID_MANIFEST.items()
            if k != field
        }
        # deep copy nested dicts
        if "runtime" in data:
            data["runtime"] = dict(data["runtime"])
        if "inputs" in data:
            data["inputs"] = dict(data["inputs"])
        if "outputs" in data:
            data["outputs"] = dict(data["outputs"])

        p = _write_manifest(data, tmp_path)
        is_valid, errors = validate(str(p))
        assert is_valid is False, f"Should fail when '{field}' is missing"
        assert any(field in msg for msg in errors), (
            f"Error should mention '{field}'; got: {errors}"
        )

    for parent, subfields in nested_required.items():
        for subfield in subfields:
            data = {k: v for k, v in _VALID_MANIFEST.items()}
            data[parent] = {
                k: v
                for k, v in data[parent].items()
                if k != subfield
            }
            p = _write_manifest(data, tmp_path)
            is_valid, errors = validate(str(p))
            assert is_valid is False, (
                f"Should fail when '{parent}.{subfield}' is missing"
            )
            dotted = f"{parent}.{subfield}"
            assert any(dotted in msg for msg in errors), (
                f"Error should mention '{dotted}'; got: {errors}"
            )


# ---------------------------------------------------------------------------
# test2 — invalid field type produces specific error (feature1:AC3)
# ---------------------------------------------------------------------------

def test_invalid_field_type(tmp_path: Path) -> None:
    """'dependencies' set to a string (not a list) produces a type error."""
    data = dict(_VALID_MANIFEST)
    data["dependencies"] = "openai"  # should be a list
    p = _write_manifest(data, tmp_path)
    is_valid, errors = validate(str(p))
    assert is_valid is False, "Expected validation to fail for wrong type"
    assert any("dependencies" in msg for msg in errors), (
        f"Error should mention 'dependencies'; got: {errors}"
    )
    assert any("list" in msg for msg in errors), (
        f"Error should mention 'list'; got: {errors}"
    )


def test_invalid_field_type_version_as_number(tmp_path: Path) -> None:
    """'version' set to a number produces a type error mentioning 'version'."""
    data = dict(_VALID_MANIFEST)
    data["version"] = 1  # should be a string
    p = _write_manifest(data, tmp_path)
    is_valid, errors = validate(str(p))
    assert is_valid is False
    assert any("version" in msg for msg in errors), (
        f"Error should mention 'version'; got: {errors}"
    )


# ---------------------------------------------------------------------------
# test3 — invalid semver format produces descriptive error (feature1:AC4)
# ---------------------------------------------------------------------------

def test_invalid_semver_format(tmp_path: Path) -> None:
    """version='1.0' (missing patch segment) produces a semver error."""
    data = dict(_VALID_MANIFEST)
    data["version"] = "1.0"  # invalid — missing patch
    p = _write_manifest(data, tmp_path)
    is_valid, errors = validate(str(p))
    assert is_valid is False, "Expected validation to fail for bad semver"
    assert any("version" in msg for msg in errors), (
        f"Error should mention 'version'; got: {errors}"
    )
    assert any("semver" in msg.lower() for msg in errors), (
        f"Error should mention 'semver'; got: {errors}"
    )


# ---------------------------------------------------------------------------
# test4 — validator return type is correct (feature1:AC5)
# ---------------------------------------------------------------------------

def test_validator_return_type(tmp_path: Path) -> None:
    """validate() returns a tuple of (bool, list[str])."""
    p = _write_manifest(_VALID_MANIFEST, tmp_path)
    result = validate(str(p))
    assert isinstance(result, tuple), "Return value must be a tuple"
    assert len(result) == 2, "Tuple must have exactly 2 elements"
    is_valid, errors = result
    assert isinstance(is_valid, bool), "First element must be a bool"
    assert isinstance(errors, list), "Second element must be a list"
    for msg in errors:
        assert isinstance(msg, str), f"Each error must be a str; got {type(msg)}"


# ---------------------------------------------------------------------------
# test5 — optional 'framework' field (feature1:AC6)
# ---------------------------------------------------------------------------

def test_framework_optional(tmp_path: Path) -> None:
    """Manifest without 'framework' and with 'framework' both pass."""
    # Without framework
    data_no_fw = dict(_VALID_MANIFEST)
    p_no_fw = tmp_path / "no_fw.yaml"
    p_no_fw.write_text(yaml.dump(data_no_fw), encoding="utf-8")
    is_valid, errors = validate(str(p_no_fw))
    assert is_valid is True, f"Manifest without 'framework' should pass; errors: {errors}"
    assert errors == []

    # With framework
    data_with_fw = dict(_VALID_MANIFEST)
    data_with_fw["framework"] = "langchain"
    p_with_fw = tmp_path / "with_fw.yaml"
    p_with_fw.write_text(yaml.dump(data_with_fw), encoding="utf-8")
    is_valid, errors = validate(str(p_with_fw))
    assert is_valid is True, f"Manifest with 'framework' should pass; errors: {errors}"
    assert errors == []


# ---------------------------------------------------------------------------
# test6 — unsupported runtime.type produces descriptive error (feature1:AC7)
# ---------------------------------------------------------------------------

def test_invalid_runtime_type(tmp_path: Path) -> None:
    """runtime.type='server' produces an error mentioning 'runtime.type' and 'one-shot'."""
    data = dict(_VALID_MANIFEST)
    data["runtime"] = dict(data["runtime"])
    data["runtime"]["type"] = "server"  # not supported in MVP
    p = _write_manifest(data, tmp_path)
    is_valid, errors = validate(str(p))
    assert is_valid is False, "Expected validation to fail for unsupported runtime.type"
    assert any("runtime.type" in msg for msg in errors), (
        f"Error should mention 'runtime.type'; got: {errors}"
    )
    assert any("one-shot" in msg for msg in errors), (
        f"Error should mention 'one-shot'; got: {errors}"
    )
