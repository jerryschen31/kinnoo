"""Import command surface for in-place onboarding workflows."""

from __future__ import annotations

from pathlib import Path


def _resolve_import_target(target_path_arg: str | None) -> Path:
    """Resolve the import target path, defaulting to the current directory."""
    if target_path_arg is None:
        return Path.cwd().resolve()
    return Path(target_path_arg).expanduser().resolve()


def import_agent(target_path_arg: str | None) -> int:
    """Validate target path and start import flow scaffolding for future tasks."""
    target_path = _resolve_import_target(target_path_arg)

    if not target_path.exists():
        print(f"Error: import target does not exist: {target_path}")
        return 1

    if not target_path.is_dir():
        print(f"Error: import target must be a directory: {target_path}")
        return 1

    # Task163 intentionally provides CLI surface and path resolution only.
    print(f"Starting import analysis for: {target_path}")
    return 0
