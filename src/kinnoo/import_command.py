"""Import command surface for in-place onboarding workflows."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_IMPORTED_MANIFEST = """name: imported-agent
version: 1.0.0
entrypoint: run.py
runtime:
    type: one-shot
    language: python
    version: \">=3.10\"
dependencies: []
inputs:
    type: string
outputs:
    type: string
"""


def _resolve_import_target(target_path_arg: str | None) -> Path:
    """Resolve the import target path, defaulting to the current directory."""
    if target_path_arg is None:
        return Path.cwd().resolve()
    return Path(target_path_arg).expanduser().resolve()


def _build_manifest_text(target_path: Path) -> str:
    """Return a deterministic baseline manifest for in-place import writes."""
    agent_name = target_path.name.replace("_", "-").lower() or "imported-agent"
    manifest = DEFAULT_IMPORTED_MANIFEST.replace("name: imported-agent", f"name: {agent_name}")
    return manifest


def _write_manifest_in_place(target_path: Path) -> None:
    manifest_path = target_path / "kinnoo.yaml"
    if manifest_path.exists():
        raise FileExistsError(
            "Import aborted: kinnoo.yaml already exists. "
            "Use an explicit override path in a later import step before overwriting."
        )

    wrote_manifest = False
    try:
        manifest_path.write_text(_build_manifest_text(target_path), encoding="utf-8")
        wrote_manifest = True

        # Test-only failure injection to prove rollback safety for task164.
        if os.getenv("KINNOO_IMPORT_FAIL_AFTER_WRITE") == "1":
            raise RuntimeError("Simulated import failure after manifest write")
    except Exception:
        if wrote_manifest and manifest_path.exists():
            manifest_path.unlink()
        raise


def import_agent(target_path_arg: str | None) -> int:
    """Import a project in-place by writing kinnoo.yaml safely into target root."""
    target_path = _resolve_import_target(target_path_arg)

    if not target_path.exists():
        print(f"Error: import target does not exist: {target_path}")
        return 1

    if not target_path.is_dir():
        print(f"Error: import target must be a directory: {target_path}")
        return 1

    try:
        _write_manifest_in_place(target_path)
    except FileExistsError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Error: import failed and rolled back partial artifacts: {exc}")
        return 1

    print(f"Imported project in-place: {target_path}")
    return 0
