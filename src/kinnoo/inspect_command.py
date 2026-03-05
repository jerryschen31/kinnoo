from __future__ import annotations

import sys
from pathlib import Path


def _print_missing_manifest_guidance() -> None:
    print("Error: Missing required file 'kinnoo.yaml' in target directory.")
    print("Create a kinnoo.yaml file before running `kinnoo inspect`.")
    print("Minimal example:")
    print("name: my-agent")
    print("version: 0.1.0")
    print("entrypoint: run.py")
    print("runtime:")
    print("  language: python")
    print("  version: \"3.10\"")
    print("  type: one-shot")
    print("dependencies: []")
    print("inputs:")
    print("  type: string")
    print("outputs:")
    print("  type: string")


def _print_missing_requirements_guidance() -> None:
    print("Error: Missing required file 'requirements.txt' in target directory.")
    print("Create requirements.txt before running `kinnoo inspect`.")
    print("Recommended generation steps:")
    print("pip install uv")
    print("uv export --format requirements-txt > requirements.txt")


def _inspect_archive_target(_archive_path: Path) -> int:
    print("Archive target detected. Archive manifest inspection is handled in task64.")
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

    try:
        manifest_path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"Error: Unable to read '{manifest_path}': {error}", file=sys.stderr)
        return 1

    print("Directory target detected. Manifest loaded for downstream inspection flow.")
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
