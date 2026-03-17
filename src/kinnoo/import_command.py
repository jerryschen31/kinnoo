"""Import command surface for in-place onboarding workflows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from kinnoo.analyzer import analyze_project
except ImportError:
    from .analyzer import analyze_project


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


def _prompt_with_default(prompt: str, default: str) -> str:
    """Read a prompt value and gracefully fallback in non-interactive test runs."""
    try:
        value = input(prompt)
    except EOFError:
        return default
    value = value.strip()
    return value if value else default


def _show_detected_values(report: dict[str, Any]) -> None:
    inferred = report.get("inferred", {})
    print("Detected values from analyzer:")
    for key in ("entrypoint", "runtime", "framework", "dependencies", "env_vars"):
        print(f"  - {key}: {inferred.get(key)}")


def _get_confidence(report: dict[str, Any], field_name: str) -> float:
    confidence_meta = report.get("confidence", {}).get(field_name, {})
    score = confidence_meta.get("score", 0.0)
    try:
        return float(score)
    except (TypeError, ValueError):
        return 0.0


def _should_prompt_field(report: dict[str, Any], field_name: str, current_value: Any) -> bool:
    if current_value in (None, ""):
        return True
    return _get_confidence(report, field_name) < 0.6


def _build_manifest_from_analysis(target_path: Path, report: dict[str, Any]) -> str:
    inferred = report.get("inferred", {})

    name = target_path.name.replace("_", "-").lower() or "imported-agent"
    entrypoint = inferred.get("entrypoint") or "run.py"

    runtime = inferred.get("runtime") if isinstance(inferred.get("runtime"), dict) else {}
    runtime_language = runtime.get("language") or "python"
    runtime_version = runtime.get("version") or ">=3.10"
    runtime_type = runtime.get("type") or "one-shot"

    framework = inferred.get("framework")
    dependencies = inferred.get("dependencies") if isinstance(inferred.get("dependencies"), list) else []
    env_vars = inferred.get("env_vars") if isinstance(inferred.get("env_vars"), list) else []

    if _should_prompt_field(report, "entrypoint", entrypoint):
        entrypoint = _prompt_with_default("Provide value for entrypoint [run.py]: ", "run.py")

    if _should_prompt_field(report, "runtime", runtime_type):
        runtime_type = _prompt_with_default("Provide value for runtime.type [one-shot]: ", "one-shot")

    if _should_prompt_field(report, "framework", framework):
        framework_input = _prompt_with_default("Provide value for framework (optional): ", "")
        framework = framework_input or None

    dependency_lines = "\n".join(f"  - {item}" for item in dependencies)
    if not dependency_lines:
        dependency_lines = "  []"

    env_lines = "\n".join(f"  - {item}" for item in env_vars)
    manifest_lines = [
        f"name: {name}",
        "version: 1.0.0",
        f"entrypoint: {entrypoint}",
        "runtime:",
        f"  type: {runtime_type}",
        f"  language: {runtime_language}",
        f"  version: \"{runtime_version}\"",
        "dependencies:",
        dependency_lines,
        "inputs:",
        "  type: string",
        "outputs:",
        "  type: string",
    ]

    if framework:
        manifest_lines.append(f"framework: {framework}")
    if env_lines:
        manifest_lines.append("env_vars:")
        manifest_lines.append(env_lines)

    return "\n".join(manifest_lines) + "\n"


def _write_manifest_in_place(target_path: Path, manifest_text: str) -> None:
    manifest_path = target_path / "kinnoo.yaml"
    if manifest_path.exists():
        raise FileExistsError(
            "Import aborted: kinnoo.yaml already exists. "
            "Use an explicit override path in a later import step before overwriting."
        )

    wrote_manifest = False
    try:
        manifest_path.write_text(manifest_text, encoding="utf-8")
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

    report = analyze_project(target_path).as_dict()
    _show_detected_values(report)

    warning_messages = report.get("warnings", [])
    if warning_messages:
        print("Analyzer warnings:")
        for warning in warning_messages:
            print(f"  - {warning}")

    confirmed = _prompt_with_default("Proceed with detected values? [Y/n]: ", "y").lower()
    if confirmed not in {"y", "yes"}:
        print("Import cancelled by user.")
        return 1

    manifest_text = _build_manifest_from_analysis(target_path, report)

    try:
        _write_manifest_in_place(target_path, manifest_text)
    except FileExistsError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Error: import failed and rolled back partial artifacts: {exc}")
        return 1

    print(f"Imported project in-place: {target_path}")
    return 0
