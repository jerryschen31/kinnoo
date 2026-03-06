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
    from kinnoo.registry import RegistryService, parse_install_target_spec
    from kinnoo.registry_backends import MockFilesystemRegistryBackend
    from kinnoo.validator import validate
except ImportError:
    from .registry import RegistryService, parse_install_target_spec
    from .registry_backends import MockFilesystemRegistryBackend
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


def _requirement_name(requirement_line: str) -> str:
    base = re.split(r"[<>=!~\[\s]", requirement_line, maxsplit=1)[0]
    return base.strip().lower().replace("_", "-")


def _wheel_distribution_name(wheel_filename: str) -> str:
    return wheel_filename.split("-", 1)[0].lower().replace("_", "-")


def _is_offline_mode_enabled() -> bool:
    # [agent] Offline mode is intentionally controlled by env vars so tests can
    # enforce deterministic no-network behavior without relying on host firewall state.
    offline_values = {"1", "true", "yes", "on"}
    kinnoo_offline = os.environ.get("KINNOO_OFFLINE", "").strip().lower()
    pip_no_index = os.environ.get("PIP_NO_INDEX", "").strip().lower()
    return kinnoo_offline in offline_values or pip_no_index in offline_values


def install_agent(archive_path: str, target_dir_arg: str | None = None, force: bool = False) -> int:
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
        )

    archive = target_spec.archive_path or Path(archive_path)
    return _install_from_archive_path(
        archive_path=str(archive),
        target_dir_arg=target_dir_arg,
        force=force,
    )


def _install_from_archive_path(
    archive_path: str,
    target_dir_arg: str | None = None,
    force: bool = False,
) -> int:
    archive = Path(archive_path)
    if not archive.exists() or not archive.is_file():
        print(f"Error: Archive '{archive}' does not exist or is not a file.", file=sys.stderr)
        return 1
    if not str(archive).endswith(".kno"):
        print(f"Error: Archive '{archive}' is not a .kno file.", file=sys.stderr)
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