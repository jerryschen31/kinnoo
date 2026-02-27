from __future__ import annotations

import shutil
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

try:
    from kinnoo.validator import validate
except ImportError:
    from .validator import validate


def install_agent(archive_path: str, target_dir_arg: str | None = None, force: bool = False) -> int:
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

    if wheels_dir.exists() and wheels_dir.is_dir():
        wheel_files = list(wheels_dir.glob("*.whl"))
        if wheel_files:
            pip_exe = venv_dir / "bin" / "pip"
            if not pip_exe.exists():
                pip_exe = venv_dir / "Scripts" / "pip.exe"
            if not pip_exe.exists():
                print(f"Error: pip not found in venv at {pip_exe}", file=sys.stderr)
                shutil.rmtree(target_dir, ignore_errors=True)
                return 1

            for wheel in wheel_files:
                print(f"[kinnoo install] Installing wheel: {wheel.name}")
                try:
                    result = subprocess.run(
                        [str(pip_exe), "install", str(wheel)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception as error:
                    print(f"Error: Failed to install wheel {wheel.name}: {error}", file=sys.stderr)
                    shutil.rmtree(target_dir, ignore_errors=True)
                    return 1

                if result.returncode != 0:
                    print(f"Error: pip install failed for {wheel.name}", file=sys.stderr)
                    shutil.rmtree(target_dir, ignore_errors=True)
                    return result.returncode

            print("[kinnoo install] All wheels installed successfully.")
        else:
            print("[kinnoo install] No wheel files found in wheels/ directory. Skipping dependency install.")
    else:
        print("[kinnoo install] No wheels/ directory found. Skipping dependency install.")

    return 0