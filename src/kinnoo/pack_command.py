"""Packaging command implementation for `kinnoo pack`."""

import os
import re
import subprocess
import sys
import tempfile
import zipfile
import json
import hashlib
from fnmatch import fnmatch
from pathlib import Path
from datetime import datetime, timezone

import yaml

from .archive import LocalArchiveBackend
from .checksum import write_checksum_sidecar_for_archive
from .code_sweep import (
    sweep_asset_credential_risks,
    sweep_env_var_exposure,
    sweep_memory_snapshot_credential_risks,
)
from .schema import normalize_env_vars
from .signing import create_detached_signature_artifacts
from .size_format import format_size_human_readable, size_in_megabytes
from .terminal_colors import style_text


def _build_archive_integrity_manifest(archive_path: Path) -> dict:
    files: dict[str, dict[str, object]] = {}
    with zipfile.ZipFile(archive_path, "r") as archive_file:
        for info in archive_file.infolist():
            if info.is_dir():
                continue
            arcname = info.filename
            if arcname.startswith("META-INF/"):
                continue
            payload = archive_file.read(arcname)
            files[arcname] = {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
            }

    return {
        "version": 1,
        "files": files,
    }

class WheelBuildError(Exception):
    pass


_CORE_SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
_DEFAULT_WARN_THRESHOLD_MB = 100.0
_NODE_METADATA_FILES = [
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "npm-shrinkwrap.json",
    "yarn.lock",
]

_OPENCLAW_IDENTITY_FILES = [
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "USER.md",
    "MEMORY.md",
    "IDENTITY.md",
    "BOOTSTRAP.md",
    "HEARTBEAT.md",
]

_OPENCLAW_WORKSPACE_DIRS = ["memory", "skills"]

_PACK_EXCLUDED_DIR_PARTS = {
    ".git",
    ".openclaw",
    "node_modules",
    ".pytest_cache",
    "__pycache__",
}

_STATE_SNAPSHOT_PREFIX = "state_snapshots"


def _warning_threshold_mb_from_env() -> float:
    raw_value = os.environ.get("KINNOO_PACK_WARN_THRESHOLD_MB")
    if raw_value is None:
        return _DEFAULT_WARN_THRESHOLD_MB

    try:
        parsed = float(raw_value)
    except ValueError:
        return _DEFAULT_WARN_THRESHOLD_MB

    if parsed <= 0:
        return _DEFAULT_WARN_THRESHOLD_MB
    return parsed


def _warning_threshold_mb_for_manifest(manifest: dict) -> float:
    assets = manifest.get("assets")
    if isinstance(assets, dict):
        asset_threshold = assets.get("max_bundle_size_mb")
        if (
            isinstance(asset_threshold, (int, float))
            and not isinstance(asset_threshold, bool)
            and asset_threshold > 0
        ):
            # Feature22: assets threshold overrides the default/env threshold.
            return float(asset_threshold)

    return _warning_threshold_mb_from_env()


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


def _path_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _contains_node_modules(relative_path: str) -> bool:
    return "node_modules" in Path(relative_path).parts


def _collect_node_metadata_files(agent_root: Path) -> list[tuple[str, Path]]:
    metadata_files: list[tuple[str, Path]] = []
    for filename in _NODE_METADATA_FILES:
        candidate = agent_root / filename
        if candidate.exists() and candidate.is_file():
            metadata_files.append((filename, candidate))
    return metadata_files


def _collect_openclaw_workspace_files(agent_root: Path) -> list[tuple[str, Path]]:
    collected: list[tuple[str, Path]] = []

    for filename in _OPENCLAW_IDENTITY_FILES:
        candidate = agent_root / filename
        if candidate.exists() and candidate.is_file():
            collected.append((filename, candidate))

    for directory_name in _OPENCLAW_WORKSPACE_DIRS:
        directory = agent_root / directory_name
        if not directory.exists() or not directory.is_dir():
            continue
        for child in sorted(directory.rglob("*")):
            if not child.is_file():
                continue
            collected.append((child.relative_to(agent_root).as_posix(), child))

    return collected


def _is_runtime_artifact_path(relative_path: str) -> bool:
    parts = Path(relative_path).parts
    return any(part in _PACK_EXCLUDED_DIR_PARTS for part in parts)


def _filter_excluded_pack_entries(
    entries: list[tuple[str, Path | str]],
) -> list[tuple[str, Path | str]]:
    filtered: list[tuple[str, Path | str]] = []
    for relative_path, absolute_path in entries:
        if _is_runtime_artifact_path(relative_path):
            continue
        filtered.append((relative_path, absolute_path))
    return filtered


def _collect_asset_files(manifest: dict, agent_root: Path) -> tuple[list[tuple[str, Path]], bool]:
    assets = manifest.get("assets")
    if not isinstance(assets, dict):
        return [], True

    bundle_enabled = assets.get("bundle", True)
    if bundle_enabled is False:
        return [], False

    declared_paths = assets.get("paths", [])
    if not isinstance(declared_paths, list):
        # Validator should prevent this; keep pack logic resilient.
        return [], True

    resolved_files: list[tuple[str, Path]] = []
    for declared in declared_paths:
        declared_path = Path(str(declared))
        candidate = (agent_root / declared_path).resolve(strict=False)
        if not _path_within_root(candidate, agent_root):
            raise ValueError(
                f"Asset path '{declared}' escapes agent directory and is not allowed."
            )

        if not candidate.exists():
            print(
                f"Warning: Declared asset path '{declared}' was not found and will be skipped.",
                file=sys.stderr,
            )
            continue

        if candidate.is_file():
            arcname = candidate.relative_to(agent_root).as_posix()
            resolved_files.append((arcname, candidate))
            continue

        if candidate.is_dir():
            for child in sorted(candidate.rglob("*")):
                if not child.is_file():
                    continue
                arcname = child.relative_to(agent_root).as_posix()
                resolved_files.append((arcname, child))

    return resolved_files, True


def _iter_declared_state_dir_paths(manifest: dict) -> list[str]:
    """Return normalized state_dirs root paths from legacy or structured entries."""
    raw_state_dirs = manifest.get("state_dirs")
    if not isinstance(raw_state_dirs, list):
        return []

    normalized_paths: list[str] = []
    for entry in raw_state_dirs:
        if isinstance(entry, str):
            candidate = entry.strip()
            if candidate:
                normalized_paths.append(candidate)
            continue

        if isinstance(entry, dict):
            path_value = entry.get("path")
            if isinstance(path_value, str):
                candidate = path_value.strip()
                if candidate:
                    normalized_paths.append(candidate)

    return normalized_paths


def _iter_declared_state_dirs_with_excludes(
    manifest: dict,
) -> list[tuple[str, list[str]]]:
    """Return normalized state_dirs entries with optional exclude patterns."""
    raw_state_dirs = manifest.get("state_dirs")
    if not isinstance(raw_state_dirs, list):
        return []

    normalized_entries: list[tuple[str, list[str]]] = []
    for entry in raw_state_dirs:
        if isinstance(entry, str):
            candidate = entry.strip()
            if candidate:
                normalized_entries.append((candidate, []))
            continue

        if not isinstance(entry, dict):
            continue

        path_value = entry.get("path")
        if not isinstance(path_value, str):
            continue

        candidate = path_value.strip()
        if not candidate:
            continue

        excludes: list[str] = []
        raw_excludes = entry.get("exclude")
        if isinstance(raw_excludes, list):
            for pattern in raw_excludes:
                if not isinstance(pattern, str):
                    continue
                normalized_pattern = pattern.strip()
                if normalized_pattern:
                    excludes.append(normalized_pattern)

        normalized_entries.append((candidate, excludes))

    return normalized_entries


def _matches_state_exclude_pattern(relative_path: str, pattern: str) -> bool:
    normalized_path = relative_path.replace("\\", "/")
    normalized_pattern = pattern.replace("\\", "/")

    if normalized_pattern.startswith("./"):
        normalized_pattern = normalized_pattern[2:]

    if normalized_pattern.endswith("/"):
        prefix = normalized_pattern.rstrip("/")
        return normalized_path == prefix or normalized_path.startswith(prefix + "/")

    return fnmatch(normalized_path, normalized_pattern)


def _is_excluded_state_snapshot_path(
    relative_path: str,
    exclude_patterns: list[str],
) -> bool:
    for pattern in exclude_patterns:
        if _matches_state_exclude_pattern(relative_path, pattern):
            return True
    return False


def _collect_state_snapshot_files(manifest: dict, agent_root: Path) -> list[tuple[str, Path]]:
    """Collect state_dirs files into deterministic snapshot archive paths.

    Layout is intentionally separated from immutable assets to preserve semantic
    distinction for future install/restore behavior.
    """
    snapshot_files: list[tuple[str, Path]] = []

    for declared_state_root, exclude_patterns in _iter_declared_state_dirs_with_excludes(
        manifest
    ):
        state_root_path = (agent_root / Path(declared_state_root)).resolve(strict=False)
        if not _path_within_root(state_root_path, agent_root):
            raise ValueError(
                f"State directory path '{declared_state_root}' escapes agent directory and is not allowed."
            )

        if not state_root_path.exists():
            print(
                f"Warning: Declared state directory '{declared_state_root}' was not found and will be skipped.",
                file=sys.stderr,
            )
            continue

        if state_root_path.is_file():
            raise ValueError(
                f"State directory path '{declared_state_root}' must reference a directory, not a file."
            )

        for child in sorted(state_root_path.rglob("*")):
            if not child.is_file():
                continue
            relative_from_state_root = child.relative_to(state_root_path).as_posix()
            if _is_excluded_state_snapshot_path(
                relative_path=relative_from_state_root,
                exclude_patterns=exclude_patterns,
            ):
                continue
            arcname = f"{_STATE_SNAPSHOT_PREFIX}/{declared_state_root}/{relative_from_state_root}"
            snapshot_files.append((arcname, child))

    return snapshot_files

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
            sys.executable, "-m", "pip", "wheel",
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


def pack_agent(
    agent_dir: str,
    bump: str | None = None,
    sign: bool = False,
    signing_key_path: str | None = None,
    preflight: bool = False,
) -> int:
    abs_agent_dir = os.path.abspath(agent_dir)
    cwd = os.path.abspath(os.getcwd())
    if abs_agent_dir == cwd or os.path.samefile(abs_agent_dir, cwd):
        print("Do not run kinnoo pack from inside the agent directory. Please navigate outside and run: kinnoo pack <agent-dir>")
        return 1
    if not os.path.isdir(abs_agent_dir):
        print(f"Error: Agent directory '{agent_dir}' does not exist.")
        return 1

    if sign and not signing_key_path:
        print("Error: --sign requires --signing-key <private-key.pem>", file=sys.stderr)
        return 1

    if not sign and signing_key_path:
        print("Error: --signing-key can only be used together with --sign", file=sys.stderr)
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

    runtime_language = "python"
    runtime_section = manifest.get("runtime") if isinstance(manifest, dict) else None
    if isinstance(runtime_section, dict):
        runtime_language_value = runtime_section.get("language")
        if isinstance(runtime_language_value, str) and runtime_language_value.strip():
            runtime_language = runtime_language_value.strip().lower()

    manifest_framework = ""
    framework_value = manifest.get("framework") if isinstance(manifest, dict) else None
    if isinstance(framework_value, str) and framework_value.strip():
        manifest_framework = framework_value.strip().lower()

    declared_env_vars = normalize_env_vars(manifest.get("env_vars") if isinstance(manifest, dict) else None)
    sweep_warnings = sweep_env_var_exposure(Path(abs_agent_dir), declared_env_vars)
    if sweep_warnings:
        print("Security sweep warnings:", file=sys.stderr)
        # [agent] SECURITY INVARIANT: only env var NAMES, never values
        for warning in sweep_warnings:
            print(f"- {warning}", file=sys.stderr)
        print(
            "(heuristic scan — may produce false positives; not a substitute for code review)",
            file=sys.stderr,
        )

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

    if preflight:
        try:
            from kinnoo.run_command import run_preflight
        except ImportError:
            from .run_command import run_preflight

        preflight_exit_code = run_preflight(abs_agent_dir)
        if preflight_exit_code == 0:
            manifest["preflight_status"] = "PASS"
            manifest["preflight_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            with open(kinnoo_yaml_path, "w", encoding="utf-8") as manifest_file:
                yaml.safe_dump(manifest, manifest_file, sort_keys=False)
        else:
            print(style_text("Warning: preflight checks failed before pack.", color="yellow"), file=sys.stderr)
            try:
                continue_response = input(style_text("Preflight failed. Continue packing anyway? [y/N]: ", color="yellow", bold=True))
            except EOFError:
                continue_response = ""

            if continue_response.strip().lower() != "y":
                print(style_text("[kinnoo pack] Aborted due to preflight failure.", color="red", bold=True))
                return 1

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
        if _is_runtime_artifact_path(relative_path):
            continue
        if runtime_language == "nodejs" and _contains_node_modules(relative_path):
            print(
                f"Warning: Skipping '{relative_path}' because node_modules must not be bundled for nodejs agents.",
                file=sys.stderr,
            )
            continue
        candidate_path = os.path.abspath(os.path.join(abs_agent_dir, relative_path))
        if not candidate_path.startswith(abs_agent_dir + os.sep):
            print(f"Error: Additional file path '{relative_path}' escapes agent directory.", file=sys.stderr)
            return 1
        if not os.path.isfile(candidate_path):
            print(f"Error: Additional file '{relative_path}' not found in {agent_dir}", file=sys.stderr)
            return 1
        safe_additional_paths.append((relative_path, candidate_path))

    try:
        asset_files, assets_bundle_enabled = _collect_asset_files(
            manifest=manifest,
            agent_root=Path(abs_agent_dir),
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    asset_files = _filter_excluded_pack_entries(asset_files)

    try:
        state_snapshot_files = _collect_state_snapshot_files(
            manifest=manifest,
            agent_root=Path(abs_agent_dir),
        )
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    state_snapshot_files = _filter_excluded_pack_entries(state_snapshot_files)

    if not assets_bundle_enabled:
        print("[kinnoo pack] Asset bundling disabled by assets.bundle=false")

    if runtime_language == "nodejs":
        filtered_asset_files: list[tuple[str, Path]] = []
        for arcname, absolute_path in asset_files:
            if _contains_node_modules(arcname):
                print(
                    f"Warning: Skipping asset '{arcname}' because node_modules must not be bundled for nodejs agents.",
                    file=sys.stderr,
                )
                continue
            filtered_asset_files.append((arcname, absolute_path))
        asset_files = filtered_asset_files

    node_metadata_files: list[tuple[str, Path]] = []
    if runtime_language == "nodejs":
        node_metadata_files = _collect_node_metadata_files(Path(abs_agent_dir))
        package_json_present = any(path == "package.json" for path, _ in node_metadata_files)
        if not package_json_present:
            print(
                "Error: Node.js agents must include package.json for reproducible install behavior.",
                file=sys.stderr,
            )
            return 1

    openclaw_workspace_files: list[tuple[str, Path]] = []
    if manifest_framework == "openclaw":
        openclaw_workspace_files = _collect_openclaw_workspace_files(Path(abs_agent_dir))
        openclaw_workspace_files = [
            (relative_path, Path(absolute_path))
            for relative_path, absolute_path in _filter_excluded_pack_entries(openclaw_workspace_files)
        ]

    asset_scan_warnings = sweep_asset_credential_risks(
        agent_dir=Path(abs_agent_dir),
        asset_file_paths=[absolute_path for _, absolute_path in asset_files],
    )
    if asset_scan_warnings:
        print("Asset security sweep warnings:", file=sys.stderr)
        for warning in asset_scan_warnings:
            print(f"- {warning}", file=sys.stderr)
        print(
            "(heuristic credential scan over assets - warning-only; may produce false positives)",
            file=sys.stderr,
        )

    memory_snapshot_scan_warnings = sweep_memory_snapshot_credential_risks(
        agent_dir=Path(abs_agent_dir),
        snapshot_candidate_paths=[absolute_path for _, absolute_path in state_snapshot_files],
    )
    if memory_snapshot_scan_warnings:
        print("Memory snapshot security sweep warnings:", file=sys.stderr)
        for warning in memory_snapshot_scan_warnings:
            print(f"- {warning}", file=sys.stderr)
        print(
            "(heuristic credential scan over memory snapshots - warning-only; may produce false positives)",
            file=sys.stderr,
        )

    print(style_text(f"[kinnoo pack] Packaging agent directory: {agent_dir}", color="cyan", bold=True))
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
        archived_entries: set[str] = set()

        archive_file.write(kinnoo_yaml_path, arcname="kinnoo.yaml")
        archived_entries.add("kinnoo.yaml")
        archive_file.write(entrypoint_path, arcname=os.path.basename(entrypoint_path))
        archived_entries.add(os.path.basename(entrypoint_path))
        archive_file.write(requirements_path, arcname="requirements.txt")
        archived_entries.add("requirements.txt")
        for relative_path, absolute_path in safe_additional_paths:
            if relative_path in archived_entries:
                continue
            archive_file.write(absolute_path, arcname=relative_path)
            archived_entries.add(relative_path)
        for arcname, absolute_path in asset_files:
            if arcname in archived_entries:
                continue
            archive_file.write(absolute_path, arcname=arcname)
            archived_entries.add(arcname)
        for arcname, absolute_path in state_snapshot_files:
            if arcname in archived_entries:
                continue
            archive_file.write(absolute_path, arcname=arcname)
            archived_entries.add(arcname)
        for relative_path, absolute_path in node_metadata_files:
            if relative_path in archived_entries:
                continue
            archive_file.write(absolute_path, arcname=relative_path)
            archived_entries.add(relative_path)
        for relative_path, absolute_path in openclaw_workspace_files:
            if relative_path in archived_entries:
                continue
            archive_file.write(absolute_path, arcname=relative_path)
            archived_entries.add(relative_path)
        for wheel_path in wheel_files:
            archive_file.write(wheel_path, arcname=f"wheels/{os.path.basename(wheel_path)}")
        if missing_wheels_report_path is not None:
            archive_file.write(missing_wheels_report_path, arcname="wheels/missing_wheels.txt")

    integrity_manifest = _build_archive_integrity_manifest(staged_archive_path)
    integrity_payload = (
        json.dumps(integrity_manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )
    # Keep integrity.json last so it covers all non-META-INF archive entries.
    with zipfile.ZipFile(staged_archive_path, "a", zipfile.ZIP_DEFLATED) as archive_file:
        archive_file.writestr("META-INF/integrity.json", integrity_payload)

    stored_record = archive_backend.store(
        name=name,
        version=version,
        source_archive=staged_archive_path,
        overwrite=True,
    )

    try:
        checksum_sidecar_path = write_checksum_sidecar_for_archive(stored_record.archive_path)
    except OSError as error:
        print(f"Error: Failed to write checksum sidecar: {error}", file=sys.stderr)
        wheels_dir.cleanup()
        return 1

    signature_result = None
    if sign:
        assert signing_key_path is not None
        try:
            signature_result = create_detached_signature_artifacts(
                archive_path=stored_record.archive_path,
                private_key_path=Path(signing_key_path).expanduser(),
            )
        except (OSError, ValueError) as error:
            print(f"Error: Failed to sign archive: {error}", file=sys.stderr)
            wheels_dir.cleanup()
            return 1

    print(style_text(f"[kinnoo pack] Archive created: {stored_record.archive_path}", color="green", bold=True))
    print(style_text(f"[kinnoo pack] Checksum sidecar written: {checksum_sidecar_path}", color="cyan"))
    if signature_result is not None:
        print(f"[kinnoo pack] Signature artifact written: {signature_result.signature_path}")
        print(f"[kinnoo pack] Signature metadata written: {signature_result.metadata_path}")
        print(
            "[kinnoo pack] Signature key fingerprint (SHA256): "
            f"{signature_result.public_key_fingerprint}"
        )
        print(
            "[kinnoo pack] Verification hint: use publisher public key in signature metadata "
            "or registry key association."
        )
    archive_size_bytes = stored_record.archive_path.stat().st_size
    archive_size_human = format_size_human_readable(archive_size_bytes)
    print(f"[kinnoo pack] Archive size: {archive_size_human}")

    warning_threshold_mb = _warning_threshold_mb_for_manifest(manifest)
    archive_size_mb = size_in_megabytes(archive_size_bytes)
    if archive_size_mb > warning_threshold_mb:
        # Keep warning text stable for docs/tests and operator guidance.
        print(
            "Warning: archive is large "
            f"({archive_size_mb:.1f} MB). Consider whether all dependencies are necessary.",
            file=sys.stderr,
        )
    print(f"[kinnoo pack] Agent version: {version}")
    wheels_dir.cleanup()
    return 0
