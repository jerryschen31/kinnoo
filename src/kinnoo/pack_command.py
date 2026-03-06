"""Packaging command implementation for `kinnoo pack`."""

import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

from .archive import LocalArchiveBackend

class WheelBuildError(Exception):
    pass


_CORE_SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _bump_core_semver(version: str, bump: str) -> str | None:
    match = _CORE_SEMVER_PATTERN.fullmatch(version.strip())
    if match is None:
        return None

    major, minor, patch = (int(part) for part in match.groups())

    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "major":
        return f"{major + 1}.0.0"

    return None


def _collect_additional_files(manifest: dict) -> list[str]:
    additional: list[str] = []

    files_field = manifest.get("files", [])
    if isinstance(files_field, list):
        additional.extend(str(path) for path in files_field)

    extra_file = manifest.get("extra_file")
    if isinstance(extra_file, str):
        additional.append(extra_file)

    return additional

def _read_requirements(requirements_path: Path) -> list[str]:
    requirements: list[str] = []
    for raw_line in requirements_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def _is_platform_specific_wheel(wheel_filename: str) -> bool:
    """Return True when wheel platform tag is not universal (`any`)."""
    if not wheel_filename.endswith(".whl"):
        return False

    stem = wheel_filename[:-4]
    parts = stem.rsplit("-", 3)
    if len(parts) != 4:
        return False

    platform_tag = parts[3]
    return platform_tag != "any"


def build_wheels(requirements_path: Path, wheels_dir: Path):
    """
    Build/download wheel files for dependencies in requirements.txt using per-dependency
    pip wheel calls so individual failures can be non-fatal.
    """
    if not requirements_path.exists() or not requirements_path.read_text().strip():
        # No requirements or empty file: nothing to do
        return [], []

    requirements = _read_requirements(requirements_path)
    if not requirements:
        return [], []

    wheels_dir.mkdir(parents=True, exist_ok=True)
    failed_requirements: list[str] = []
    for requirement in requirements:
        cmd = [
            "python3", "-m", "pip", "wheel",
            requirement,
            "--wheel-dir", str(wheels_dir),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            failed_requirements.append(requirement)
            print(
                f"Warning: Could not build wheel for dependency '{requirement}'. "
                "Packaging will continue and install may require PyPI fallback.",
                file=sys.stderr,
            )

    return list(wheels_dir.glob("*.whl")), failed_requirements


def pack_agent(agent_dir: str, bump: str | None = None) -> int:
    abs_agent_dir = os.path.abspath(agent_dir)
    cwd = os.path.abspath(os.getcwd())
    if abs_agent_dir == cwd or os.path.samefile(abs_agent_dir, cwd):
        print("Do not run kinnoo pack from inside the agent directory. Please navigate outside and run: kinnoo pack <agent-dir>")
        return 1
    if not os.path.isdir(abs_agent_dir):
        print(f"Error: Agent directory '{agent_dir}' does not exist.")
        return 1

    kinnoo_yaml_path = os.path.join(abs_agent_dir, "kinnoo.yaml")
    if not os.path.isfile(kinnoo_yaml_path):
        print(f"Error: kinnoo.yaml not found in {agent_dir}", file=sys.stderr)
        return 1

    try:
        from kinnoo.validator import validate
    except ImportError:
        from .validator import validate

    try:
        is_valid, errors = validate(kinnoo_yaml_path)
    except Exception as error:
        print(f"Error: Failed to validate kinnoo.yaml: {error}", file=sys.stderr)
        return 1

    if not is_valid:
        print("Manifest validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    with open(kinnoo_yaml_path, "r") as manifest_file:
        manifest = yaml.safe_load(manifest_file)

    name = manifest.get("name")
    if not isinstance(name, str) or not name.strip():
        print("Error: 'name' must be a non-empty string in kinnoo.yaml", file=sys.stderr)
        return 1
    name = name.strip()

    version = manifest.get("version")
    if not isinstance(version, str):
        print("Error: 'version' must be a string in kinnoo.yaml", file=sys.stderr)
        return 1

    if bump is not None:
        bumped_version = _bump_core_semver(version, bump)
        if bumped_version is None:
            print(
                "Error: --bump requires a core semver version in format x.y.z",
                file=sys.stderr,
            )
            return 1
        manifest["version"] = bumped_version
        version = bumped_version
        with open(kinnoo_yaml_path, "w", encoding="utf-8") as manifest_file:
            yaml.safe_dump(manifest, manifest_file, sort_keys=False)

    entrypoint = manifest.get("entrypoint")
    if not entrypoint:
        print("Error: 'entrypoint' not specified in kinnoo.yaml", file=sys.stderr)
        return 1

    entrypoint_path = os.path.join(abs_agent_dir, entrypoint)
    if not os.path.isfile(entrypoint_path):
        print(f"Error: Entrypoint file '{entrypoint}' not found in {agent_dir}", file=sys.stderr)
        return 1

    requirements_path = os.path.join(abs_agent_dir, "requirements.txt")
    if not os.path.isfile(requirements_path):
        print(f"Error: requirements.txt not found in {agent_dir}", file=sys.stderr)
        return 1

    additional_files = _collect_additional_files(manifest)
    safe_additional_paths: list[tuple[str, str]] = []
    for relative_path in additional_files:
        candidate_path = os.path.abspath(os.path.join(abs_agent_dir, relative_path))
        if not candidate_path.startswith(abs_agent_dir + os.sep):
            print(f"Error: Additional file path '{relative_path}' escapes agent directory.", file=sys.stderr)
            return 1
        if not os.path.isfile(candidate_path):
            print(f"Error: Additional file '{relative_path}' not found in {agent_dir}", file=sys.stderr)
            return 1
        safe_additional_paths.append((relative_path, candidate_path))

    print(f"[kinnoo pack] Packaging agent directory: {agent_dir}")
    wheels_dir = tempfile.TemporaryDirectory(prefix="kinnoo_wheels_")

    wheel_files, failed_requirements = build_wheels(Path(requirements_path), Path(wheels_dir.name))

    platform_specific_wheels = [wheel.name for wheel in wheel_files if _is_platform_specific_wheel(wheel.name)]
    if platform_specific_wheels:
        print(
            "Warning: Archive contains platform-specific wheels that may not install on other operating systems.",
            file=sys.stderr,
        )
        print(
            "Warning: Platform-specific wheel files: "
            f"{', '.join(sorted(platform_specific_wheels))}",
            file=sys.stderr,
        )

    missing_wheels_report_path: str | None = None
    if failed_requirements:
        missing_wheels_report_path = os.path.join(wheels_dir.name, "missing_wheels.txt")
        with open(missing_wheels_report_path, "w", encoding="utf-8") as report_file:
            report_file.write("\n".join(failed_requirements) + "\n")
        print(
            "Warning: Some dependency wheels could not be bundled: "
            f"{', '.join(failed_requirements)}",
            file=sys.stderr,
        )

    archive_root = os.environ.get("KINNOO_ARCHIVE_ROOT")
    archive_backend = LocalArchiveBackend(
        root=Path(archive_root).expanduser() if archive_root else None
    )
    archive_path = archive_backend.archive_path_for(name=name, version=version)
    archive_name = archive_path.name

    if archive_path.exists():
        try:
            overwrite_response = input(
                f"({archive_name}) already exists - are you sure you want to overwrite? (y/n): "
            )
        except EOFError:
            overwrite_response = ""

        if overwrite_response.strip().lower() != "y":
            print("[kinnoo pack] Aborted: existing archive not overwritten.")
            wheels_dir.cleanup()
            return 1

    staged_archive_path = Path(wheels_dir.name) / archive_name
    with zipfile.ZipFile(staged_archive_path, "w", zipfile.ZIP_DEFLATED) as archive_file:
        archive_file.write(kinnoo_yaml_path, arcname="kinnoo.yaml")
        archive_file.write(entrypoint_path, arcname=os.path.basename(entrypoint_path))
        archive_file.write(requirements_path, arcname="requirements.txt")
        for relative_path, absolute_path in safe_additional_paths:
            archive_file.write(absolute_path, arcname=relative_path)
        for wheel_path in wheel_files:
            archive_file.write(wheel_path, arcname=f"wheels/{os.path.basename(wheel_path)}")
        if missing_wheels_report_path is not None:
            archive_file.write(missing_wheels_report_path, arcname="wheels/missing_wheels.txt")

    stored_record = archive_backend.store(
        name=name,
        version=version,
        source_archive=staged_archive_path,
        overwrite=True,
    )

    print(f"[kinnoo pack] Archive created: {stored_record.archive_path}")
    print(f"[kinnoo pack] Agent version: {version}")
    wheels_dir.cleanup()
    return 0
