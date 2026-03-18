from __future__ import annotations

import shutil
import subprocess
import sys
import venv
import zipfile
import re
import os
from pathlib import Path

try:
    from kinnoo.checksum import (
        ChecksumParseError,
        checksum_sidecar_path_for_archive,
        read_checksum_sidecar,
        verify_archive_checksum,
    )
    from kinnoo.registry import RegistryService, parse_install_target_spec
    from kinnoo.registry_backends import MockFilesystemRegistryBackend
    from kinnoo.health_check import check_node_package_manager_availability, check_node_runtime_constraint
    from kinnoo.schema import SUPPORTED_NODE_PACKAGE_MANAGERS, normalize_env_vars
    from kinnoo.inspect_command import read_manifest_from_kno_archive
    from kinnoo.validator import validate
except ImportError:
    from .checksum import (
        ChecksumParseError,
        checksum_sidecar_path_for_archive,
        read_checksum_sidecar,
        verify_archive_checksum,
    )
    from .registry import RegistryService, parse_install_target_spec
    from .registry_backends import MockFilesystemRegistryBackend
    from .health_check import check_node_package_manager_availability, check_node_runtime_constraint
    from .schema import SUPPORTED_NODE_PACKAGE_MANAGERS, normalize_env_vars
    from .inspect_command import read_manifest_from_kno_archive
    from .validator import validate


def _read_requirements(requirements_path: Path) -> list[str]:
    requirements: list[str] = []
    if not requirements_path.exists():
        return requirements
    for raw_line in requirements_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def _read_requirements_from_archive(archive_path: Path) -> list[str]:
    requirements: list[str] = []
    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            requirements_members = [
                member_name
                for member_name in archive_zip.namelist()
                if Path(member_name).name == "requirements.txt"
            ]
            if not requirements_members:
                return requirements

            with archive_zip.open(requirements_members[0]) as requirements_file:
                requirements_text = requirements_file.read().decode("utf-8")
    except Exception:
        return requirements

    for raw_line in requirements_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def _requirement_name(requirement_line: str) -> str:
    base = re.split(r"[<>=!~\[\s]", requirement_line, maxsplit=1)[0]
    return base.strip().lower().replace("_", "-")


def _requirement_display_name(requirement_line: str) -> str:
    base = re.split(r"[<>=!~\[\s]", requirement_line, maxsplit=1)[0]
    return base.strip()


def _wheel_distribution_name(wheel_filename: str) -> str:
    return wheel_filename.split("-", 1)[0].lower().replace("_", "-")


def _is_offline_mode_enabled() -> bool:
    # [agent] Offline mode is intentionally controlled by env vars so tests can
    # enforce deterministic no-network behavior without relying on host firewall state.
    offline_values = {"1", "true", "yes", "on"}
    kinnoo_offline = os.environ.get("KINNOO_OFFLINE", "").strip().lower()
    pip_no_index = os.environ.get("PIP_NO_INDEX", "").strip().lower()
    return kinnoo_offline in offline_values or pip_no_index in offline_values


def _resolve_node_package_manager(runtime: dict[str, object]) -> tuple[str | None, str | None]:
    package_manager_value = runtime.get("package_manager")
    if package_manager_value is None:
        return "npm", None

    if not isinstance(package_manager_value, str) or not package_manager_value.strip():
        return None, "runtime.package_manager must be a non-empty string when provided for nodejs runtime"

    normalized = package_manager_value.strip().lower()
    if normalized not in SUPPORTED_NODE_PACKAGE_MANAGERS:
        supported = ", ".join(SUPPORTED_NODE_PACKAGE_MANAGERS)
        return None, (
            f"runtime.package_manager '{package_manager_value}' is not supported. "
            f"Supported values: {supported}"
        )

    return normalized, None


def _install_node_dependencies(target_dir: Path, runtime: dict[str, object]) -> int:
    runtime_version = runtime.get("version")
    runtime_constraint = str(runtime_version) if runtime_version is not None else ""
    runtime_ok, runtime_message = check_node_runtime_constraint(runtime_constraint)
    if not runtime_ok:
        print(f"Error: {runtime_message}", file=sys.stderr)
        print(
            "Error: Install a compatible Node.js runtime and retry installation.",
            file=sys.stderr,
        )
        return 1

    package_manager, resolution_error = _resolve_node_package_manager(runtime)
    if package_manager is None:
        print(f"Error: {resolution_error}", file=sys.stderr)
        return 1

    package_manager_ok, package_manager_message = check_node_package_manager_availability(package_manager)
    if not package_manager_ok:
        print(f"Error: {package_manager_message}", file=sys.stderr)
        print(
            "Error: Install the configured package manager and ensure it is available on PATH.",
            file=sys.stderr,
        )
        return 1

    package_json_path = target_dir / "package.json"
    if not package_json_path.exists():
        print(
            "Error: Node.js runtime install requires package.json in the extracted agent directory.",
            file=sys.stderr,
        )
        return 1

    install_command = [package_manager, "install"]
    install_result = subprocess.run(
        install_command,
        capture_output=True,
        text=True,
        cwd=target_dir,
    )
    if install_result.returncode != 0:
        command_label = " ".join(install_command)
        print(
            f"Error: Node dependency installation failed while running '{command_label}'. "
            "Verify your package manager setup and package.json dependencies.",
            file=sys.stderr,
        )
        if install_result.stderr:
            print(install_result.stderr, file=sys.stderr)
        return install_result.returncode

    print(f"[kinnoo install] Node dependencies installed successfully via {package_manager}.")
    return 0


def install_agent(
    archive_path: str,
    target_dir_arg: str | None = None,
    force: bool = False,
    assume_yes: bool = False,
) -> int:
    target_spec = parse_install_target_spec(archive_path)
    if target_spec.kind == "invalid":
        print(f"Error: {target_spec.error}", file=sys.stderr)
        return 1

    if target_spec.kind in {"registry-latest", "registry-exact"}:
        selector = str(target_spec.name)
        version: str | None = None
        if target_spec.kind == "registry-exact":
            version = target_spec.version
            selector = f"{target_spec.name}=={target_spec.version}"

        registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
        backend_root = Path(registry_root).expanduser() if registry_root else None
        backend = MockFilesystemRegistryBackend(root=backend_root)
        service = RegistryService(backend=backend)

        resolved_record, resolve_error = service.resolve_with_error(
            name=str(target_spec.name),
            version=version,
        )
        if resolved_record is None:
            print(f"Error: {resolve_error or 'Registry resolution failed.'}", file=sys.stderr)
            return 1

        resolved_target_dir_arg = target_dir_arg
        if resolved_target_dir_arg is None:
            if version is None:
                resolved_target_dir_arg = str(Path.cwd() / str(target_spec.name))
            else:
                resolved_target_dir_arg = str(Path.cwd() / f"{target_spec.name}-{version}")

        print(
            f"[kinnoo install] Resolved registry selector '{selector}' to '{resolved_record.archive_path}'"
        )
        return _install_from_archive_path(
            archive_path=str(resolved_record.archive_path),
            target_dir_arg=resolved_target_dir_arg,
            force=force,
            assume_yes=assume_yes,
        )

    archive = target_spec.archive_path or Path(archive_path)
    return _install_from_archive_path(
        archive_path=str(archive),
        target_dir_arg=target_dir_arg,
        force=force,
        assume_yes=assume_yes,
    )


def _install_from_archive_path(
    archive_path: str,
    target_dir_arg: str | None = None,
    force: bool = False,
    assume_yes: bool = False,
) -> int:
    archive = Path(archive_path)
    if not archive.exists() or not archive.is_file():
        print(f"Error: Archive '{archive}' does not exist or is not a file.", file=sys.stderr)
        return 1
    if not str(archive).endswith(".kno"):
        print(f"Error: Archive '{archive}' is not a .kno file.", file=sys.stderr)
        return 1

    checksum_path = checksum_sidecar_path_for_archive(archive)
    if checksum_path.exists():
        try:
            expected_checksum, expected_archive_filename = read_checksum_sidecar(checksum_path)
        except (OSError, ChecksumParseError) as error:
            print(f"Error: Failed to read checksum sidecar: {error}", file=sys.stderr)
            return 1

        if expected_archive_filename != archive.name:
            print(
                "Error: Checksum sidecar filename does not match archive filename.",
                file=sys.stderr,
            )
            return 1

        # [agent] Integrity verification must occur before extraction/write side effects.
        checksum_matches, _ = verify_archive_checksum(archive, expected_checksum)
        if not checksum_matches:
            print(
                "Archive integrity check failed — the file may be corrupted or tampered with",
                file=sys.stderr,
            )
            return 1

        print("[kinnoo install] Archive checksum verified.")

    source_is_unverified = not checksum_path.exists()
    if source_is_unverified:
        print("No checksum file found — archive integrity not verified", file=sys.stderr)
        warning_message = "This agent is from an unverified source."
        print(warning_message, file=sys.stderr)
        if not assume_yes:
            try:
                unverified_confirmation = input(
                    "This agent is from an unverified source. Continue? (y/n): "
                ).strip().lower()
            except EOFError:
                print("Install aborted by user.", file=sys.stderr)
                return 1
            if unverified_confirmation not in {"y", "yes"}:
                print("Install aborted by user.", file=sys.stderr)
                return 1

    manifest_data = read_manifest_from_kno_archive(archive)
    if manifest_data is None:
        return 1

    runtime_type = "unknown"
    runtime = manifest_data.get("runtime")
    if isinstance(runtime, dict):
        runtime_type_value = runtime.get("type")
        if isinstance(runtime_type_value, str) and runtime_type_value.strip():
            runtime_type = runtime_type_value

    agent_name = str(manifest_data.get("name", "unknown"))
    agent_version = str(manifest_data.get("version", "unknown"))
    env_var_names = normalize_env_vars(manifest_data.get("env_vars"))
    requirement_lines = _read_requirements_from_archive(archive)
    dependency_names = [_requirement_display_name(line) for line in requirement_lines]

    print("[kinnoo install] Install summary:")
    print(f"- Agent: {agent_name}")
    print(f"- Version: {agent_version}")
    print(f"- Runtime Type: {runtime_type}")
    if dependency_names:
        print("- Dependencies:")
        for dependency_name in dependency_names:
            print(f"  - {dependency_name}")
    else:
        print("- Dependencies: (none)")
    if env_var_names:
        # [agent] SECURITY INVARIANT: only env var NAMES, never values
        print("- Env Vars:")
        for env_var_name in env_var_names:
            print(f"  - {env_var_name}")
    else:
        print("- Env Vars: (none)")

    if not assume_yes:
        try:
            confirmation = input("Continue with install? [y/N]: ").strip().lower()
        except EOFError:
            print("Install aborted by user.", file=sys.stderr)
            return 1
        if confirmation not in {"y", "yes"}:
            print("Install aborted by user.", file=sys.stderr)
            return 1

    if target_dir_arg:
        target_dir = Path(target_dir_arg).resolve()
    else:
        target_dir = archive.with_suffix("")

    if not str(target_dir) or str(target_dir) in ["/", "", "."]:
        print(f"Error: Invalid target directory '{target_dir}'.", file=sys.stderr)
        return 1

    if target_dir.exists() and not force:
        print(f"Error: Target directory '{target_dir}' already exists. Aborting to prevent overwrite.", file=sys.stderr)
        return 1
    if target_dir.exists() and force:
        try:
            shutil.rmtree(target_dir)
        except Exception as error:
            print(f"Error: Failed to remove existing directory '{target_dir}': {error}", file=sys.stderr)
            return 1

    try:
        with zipfile.ZipFile(archive, "r") as archive_zip:
            archive_zip.extractall(target_dir)
    except zipfile.BadZipFile:
        print(f"Error: Archive '{archive}' is not a valid .kno (zip) archive.", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Error: Failed to extract archive: {error}", file=sys.stderr)
        return 1

    print(f"[kinnoo install] Extracted '{archive.name}' to '{target_dir}'")

    kinnoo_yaml_path = target_dir / "kinnoo.yaml"
    if not kinnoo_yaml_path.exists():
        print(f"Error: kinnoo.yaml not found in extracted directory '{target_dir}'. Aborting install.", file=sys.stderr)
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    try:
        is_valid, errors = validate(str(kinnoo_yaml_path))
    except Exception as error:
        print(f"Error: Failed to validate kinnoo.yaml: {error}", file=sys.stderr)
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    if not is_valid:
        print("Manifest validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    print("[kinnoo install] Manifest validated successfully.")

    runtime_language = "python"
    if isinstance(runtime, dict):
        runtime_language_value = runtime.get("language")
        if isinstance(runtime_language_value, str) and runtime_language_value.strip():
            runtime_language = runtime_language_value.strip().lower()

    if runtime_language == "nodejs":
        return _install_node_dependencies(target_dir=target_dir, runtime=runtime if isinstance(runtime, dict) else {})

    wheels_dir = target_dir / "wheels"
    venv_dir = target_dir / ".venv"

    if not venv_dir.exists():
        try:
            venv.create(venv_dir, with_pip=True)
        except Exception as error:
            print(f"Error: Failed to create venv in '{venv_dir}': {error}", file=sys.stderr)
            shutil.rmtree(target_dir, ignore_errors=True)
            return 1

    pip_exe = venv_dir / "bin" / "pip"
    if not pip_exe.exists():
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    if not pip_exe.exists():
        print(f"Error: pip not found in venv at {pip_exe}", file=sys.stderr)
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    wheel_files: list[Path] = []
    if wheels_dir.exists() and wheels_dir.is_dir():
        wheel_files = list(wheels_dir.glob("*.whl"))

    requirements_path = target_dir / "requirements.txt"
    requirements = _read_requirements(requirements_path)
    if not requirements:
        if wheel_files:
            for wheel in wheel_files:
                print(f"[kinnoo install] Installing wheel: {wheel.name}")
                wheel_install = subprocess.run(
                    [str(pip_exe), "install", str(wheel)],
                    capture_output=True,
                    text=True,
                )
                if wheel_install.returncode != 0:
                    print(f"Error: pip install failed for {wheel.name}", file=sys.stderr)
                    if wheel_install.stderr:
                        print(wheel_install.stderr, file=sys.stderr)
                    shutil.rmtree(target_dir, ignore_errors=True)
                    return wheel_install.returncode
            print("[kinnoo install] All wheels installed successfully.")
        else:
            print("[kinnoo install] No dependencies listed in requirements.txt. Skipping dependency install.")
        return 0

    offline_mode_enabled = _is_offline_mode_enabled()

    expected_distributions = {_requirement_name(item) for item in requirements}
    available_distributions = {_wheel_distribution_name(wheel.name) for wheel in wheel_files}
    missing_distributions = sorted(expected_distributions - available_distributions)

    needs_pypi_fallback = bool(missing_distributions)
    if missing_distributions:
        print(
            "Warning: Missing packaged wheels for dependencies: "
            f"{', '.join(missing_distributions)}. Falling back to PyPI; internet access is required.",
            file=sys.stderr,
        )

    local_install_attempted = False
    if wheel_files:
        local_install_attempted = True
        local_install = subprocess.run(
            [
                str(pip_exe),
                "install",
                "--no-index",
                "--find-links",
                str(wheels_dir),
                "-r",
                str(requirements_path),
            ],
            capture_output=True,
            text=True,
        )
        if local_install.returncode != 0:
            needs_pypi_fallback = True
            print(
                "Warning: Local wheel-only installation failed. Falling back to PyPI; internet access is required.",
                file=sys.stderr,
            )
    else:
        needs_pypi_fallback = True
        print(
            "Warning: No bundled wheels were found. Falling back to PyPI; internet access is required.",
            file=sys.stderr,
        )

    if needs_pypi_fallback and offline_mode_enabled:
        if missing_distributions:
            print(
                "Error: Offline install requested, but packaged wheels are missing for: "
                f"{', '.join(missing_distributions)}. "
                "Rebuild the archive with complete wheels or disable offline mode.",
                file=sys.stderr,
            )
        else:
            print(
                "Error: Offline install requested, and bundled wheel-only installation failed. "
                "Rebuild the archive with complete compatible wheels or disable offline mode.",
                file=sys.stderr,
            )
        shutil.rmtree(target_dir, ignore_errors=True)
        return 1

    if needs_pypi_fallback:
        fallback_install = subprocess.run(
            [str(pip_exe), "install", "-r", str(requirements_path)],
            capture_output=True,
            text=True,
        )
        if fallback_install.returncode != 0:
            print(
                "Error: PyPI fallback installation failed.",
                file=sys.stderr,
            )
            if fallback_install.stderr:
                print(fallback_install.stderr, file=sys.stderr)
            shutil.rmtree(target_dir, ignore_errors=True)
            return fallback_install.returncode
        print("[kinnoo install] Dependencies installed via PyPI fallback.")
    elif local_install_attempted:
        print("[kinnoo install] Dependencies installed successfully from bundled wheels.")
        print("[kinnoo install] Offline-ready install path used (no network fallback required).")

    return 0