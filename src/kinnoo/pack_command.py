"""Packaging command implementation for `kinnoo pack`."""

import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

class WheelBuildError(Exception):
    pass


def _collect_additional_files(manifest: dict) -> list[str]:
    additional: list[str] = []

    files_field = manifest.get("files", [])
    if isinstance(files_field, list):
        additional.extend(str(path) for path in files_field)

    extra_file = manifest.get("extra_file")
    if isinstance(extra_file, str):
        additional.append(extra_file)

    return additional

def build_wheels(requirements_path: Path, wheels_dir: Path):
    """
    Build/download wheel files for all dependencies in requirements.txt using pip wheel.
    Wheels are stored in wheels_dir. Raises WheelBuildError on failure.
    """
    if not requirements_path.exists() or not requirements_path.read_text().strip():
        # No requirements or empty file: nothing to do
        return []
    wheels_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python3", "-m", "pip", "wheel",
        "-r", str(requirements_path),
        "--wheel-dir", str(wheels_dir)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise WheelBuildError(f"Failed to build wheels:\n{result.stderr}")
    # Return list of wheel files
    return list(wheels_dir.glob("*.whl"))


def pack_agent(agent_dir: str) -> int:
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

    try:
        wheel_files = build_wheels(Path(requirements_path), Path(wheels_dir.name))
    except WheelBuildError as error:
        print(f"Error: {error}", file=sys.stderr)
        wheels_dir.cleanup()
        return 1

    archive_name = os.path.basename(abs_agent_dir.rstrip(os.sep)) + ".kno"
    archive_path = os.path.join(os.path.dirname(abs_agent_dir), archive_name)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive_file:
        archive_file.write(kinnoo_yaml_path, arcname="kinnoo.yaml")
        archive_file.write(entrypoint_path, arcname=os.path.basename(entrypoint_path))
        archive_file.write(requirements_path, arcname="requirements.txt")
        for relative_path, absolute_path in safe_additional_paths:
            archive_file.write(absolute_path, arcname=relative_path)
        for wheel_path in wheel_files:
            archive_file.write(wheel_path, arcname=f"wheels/{os.path.basename(wheel_path)}")

    print(f"[kinnoo pack] Archive created: {archive_path}")
    wheels_dir.cleanup()
    return 0
