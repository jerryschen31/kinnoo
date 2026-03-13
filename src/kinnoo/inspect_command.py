from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import Any

import yaml

try:
    from kinnoo.checksum import ChecksumParseError, read_checksum_sidecar
    from kinnoo.code_sweep import sweep_env_var_exposure
    from kinnoo.schema import normalize_manifest_defaults, normalize_type_field
    from kinnoo.size_format import format_size_human_readable
    from kinnoo.templates import (
        INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE,
        INSPECT_MISSING_REQUIREMENTS_GUIDANCE_LINES,
    )
    from kinnoo.validator import validate_manifest_data
except ImportError:
    from .checksum import ChecksumParseError, read_checksum_sidecar
    from .code_sweep import sweep_env_var_exposure
    from .schema import normalize_manifest_defaults, normalize_type_field
    from .size_format import format_size_human_readable
    from .templates import (
        INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE,
        INSPECT_MISSING_REQUIREMENTS_GUIDANCE_LINES,
    )
    from .validator import validate_manifest_data


def _print_missing_manifest_guidance() -> None:
    print("Error: Missing required file 'kinnoo.yaml' in target directory.")
    print("Create a kinnoo.yaml file before running `kinnoo inspect`.")
    print("Minimal example:")
    print(INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE, end="")


def _print_missing_requirements_guidance() -> None:
    print("Error: Missing required file 'requirements.txt' in target directory.")
    print("Create requirements.txt before running `kinnoo inspect`.")
    for guidance_line in INSPECT_MISSING_REQUIREMENTS_GUIDANCE_LINES:
        print(guidance_line)


def read_manifest_from_kno_archive(archive_path: Path) -> dict[str, object] | None:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            manifest_members = [
                member_name
                for member_name in archive_zip.namelist()
                if Path(member_name).name == "kinnoo.yaml"
            ]

            if not manifest_members:
                print(
                    "Error: kinnoo.yaml not found inside archive. Ensure the .kno contains a manifest file.",
                    file=sys.stderr,
                )
                return None

            manifest_member = manifest_members[0]
            with archive_zip.open(manifest_member) as manifest_file:
                manifest_bytes = manifest_file.read()
    except zipfile.BadZipFile:
        print(
            f"Error: Archive '{archive_path}' is not a valid zip-based .kno file.",
            file=sys.stderr,
        )
        return None
    except OSError as error:
        print(f"Error: Failed reading archive '{archive_path}': {error}", file=sys.stderr)
        return None

    try:
        manifest_text = manifest_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        print(f"Error: Unable to decode kinnoo.yaml from archive: {error}", file=sys.stderr)
        return None

    try:
        manifest_data = yaml.safe_load(manifest_text)
    except yaml.YAMLError as error:
        print(f"Error: Failed to parse kinnoo.yaml from archive: {error}", file=sys.stderr)
        return None

    if not isinstance(manifest_data, dict):
        print("Error: kinnoo.yaml inside archive must parse to a mapping/object.", file=sys.stderr)
        return None

    return manifest_data


def _load_manifest_from_directory(manifest_path: Path) -> dict[str, Any] | None:
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Error: Unable to read '{manifest_path}': {error}", file=sys.stderr)
        return None

    try:
        manifest_data = yaml.safe_load(manifest_text)
    except yaml.YAMLError as error:
        print(f"Error: Failed to parse '{manifest_path.name}': {error}", file=sys.stderr)
        return None

    if not isinstance(manifest_data, dict):
        print(
            f"Error: '{manifest_path.name}' must parse to a mapping/object.",
            file=sys.stderr,
        )
        return None

    return manifest_data


def _normalize_manifest_for_display(manifest_data: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_manifest_defaults(dict(manifest_data))
    if "inputs" in normalized and isinstance(normalized["inputs"], dict):
        normalize_type_field(normalized["inputs"])
    if "outputs" in normalized and isinstance(normalized["outputs"], dict):
        normalize_type_field(normalized["outputs"])
    return normalized


def _print_manifest_validation_errors(errors: list[str]) -> None:
    print("Error: Manifest validation failed.", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)


def _env_var_names_for_display(manifest_data: dict[str, Any]) -> list[str]:
    env_vars = manifest_data.get("env_vars")
    if not isinstance(env_vars, list):
        return []

    names: list[str] = []
    for env_var in env_vars:
        if isinstance(env_var, str) and env_var.strip():
            names.append(env_var)

    return names


def _archive_checksum_for_display(archive_path: Path) -> str | None:
    sidecar_path = archive_path.with_name(f"{archive_path.name}.sha256")
    if not sidecar_path.exists():
        return None

    try:
        expected_checksum, referenced_filename = read_checksum_sidecar(sidecar_path)
    except (OSError, ChecksumParseError):
        return None

    if referenced_filename != archive_path.name:
        return None

    return expected_checksum


def _print_inspect_output(
    target_label: str,
    manifest_data: dict[str, Any],
    archive_checksum: str | None = None,
    archive_size_human: str | None = None,
) -> None:
    normalized = _normalize_manifest_for_display(manifest_data)

    print(f"Inspect target type: {target_label}")
    print("Manifest metadata:")
    print(f"- Name: {normalized['name']}")
    print(f"- Version: {normalized['version']}")
    print(f"- Runtime Type: {normalized['runtime']['type']}")
    if archive_size_human is not None:
        print(f"- Archive Size: {archive_size_human}")
    if archive_checksum is not None:
        print(f"- Checksum (SHA256): {archive_checksum}")

    dependencies = normalized.get("dependencies", [])
    if dependencies:
        print("- Dependencies:")
        for dependency in dependencies:
            print(f"  - {dependency}")
    else:
        print("- Dependencies: (none)")

    optional_scalar_fields = (
        ("description", "Description"),
        ("author", "Author"),
        ("license", "License"),
    )
    for field_name, label in optional_scalar_fields:
        value = normalized.get(field_name)
        if isinstance(value, str) and value.strip():
            print(f"- {label}: {value}")

    if "env_vars" in normalized:
        env_var_names = _env_var_names_for_display(normalized)
        if env_var_names:
            # [agent] SECURITY INVARIANT: only env var NAMES, never values
            print("- Env Vars:")
            for env_var_name in env_var_names:
                print(f"  - {env_var_name}")
        else:
            print("- Env Vars: (none)")


def _inspect_archive_target(archive_path: Path) -> int:
    manifest_data = read_manifest_from_kno_archive(archive_path)
    if manifest_data is None:
        return 1

    is_valid, errors = validate_manifest_data(manifest_data)
    if not is_valid:
        _print_manifest_validation_errors(errors)
        return 1

    archive_size_human = format_size_human_readable(archive_path.stat().st_size)
    archive_checksum = _archive_checksum_for_display(archive_path)
    _print_inspect_output(
        "archive (.kno)",
        manifest_data,
        archive_checksum=archive_checksum,
        archive_size_human=archive_size_human,
    )

    return 0


def _inspect_directory_target(directory_path: Path) -> int:
    manifest_path = directory_path / "kinnoo.yaml"
    requirements_path = directory_path / "requirements.txt"

    if not manifest_path.exists():
        _print_missing_manifest_guidance()
        return 1

    if not requirements_path.exists():
        _print_missing_requirements_guidance()
        return 1

    manifest_data = _load_manifest_from_directory(manifest_path)
    if manifest_data is None:
        return 1

    is_valid, errors = validate_manifest_data(manifest_data)
    if not is_valid:
        _print_manifest_validation_errors(errors)
        return 1

    _print_inspect_output("directory", manifest_data)

    declared_env_vars = _env_var_names_for_display(_normalize_manifest_for_display(manifest_data))
    sweep_warnings = sweep_env_var_exposure(directory_path, declared_env_vars)
    if sweep_warnings:
        print("Security sweep:")
        # [agent] SECURITY INVARIANT: only env var NAMES, never values
        for warning in sweep_warnings:
            print(f"- {warning}")
    else:
        print("Security sweep: no env var exposure patterns detected (heuristic)")
    print("(heuristic scan — may produce false positives; not a substitute for code review)")

    return 0


def inspect_target(target_arg: str) -> int:
    target = Path(target_arg)
    if not target.exists():
        print(f"Error: Inspect target '{target}' does not exist.", file=sys.stderr)
        return 1

    if target.is_dir():
        return _inspect_directory_target(target)

    if target.is_file():
        if target.suffix.lower() == ".kno":
            return _inspect_archive_target(target)

        print(
            f"Error: Unsupported inspect target file '{target}'. Expected an agent directory or .kno archive.",
            file=sys.stderr,
        )
        return 1

    print(f"Error: Inspect target '{target}' is neither a directory nor a regular file.", file=sys.stderr)
    return 1
