"""Import command surface for in-place onboarding workflows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

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


class ImportWizardInterrupted(Exception):
    """Raised when import wizard input is interrupted by EOF or Ctrl+C."""


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
    """Read a prompt value and raise when wizard interaction is interrupted."""
    try:
        value = input(prompt)
    except EOFError as exc:
        raise ImportWizardInterrupted("EOF") from exc
    except KeyboardInterrupt as exc:
        raise ImportWizardInterrupted("CTRL_C") from exc
    value = value.strip()
    return value if value else default


def _show_detected_values(report: dict[str, Any]) -> None:
    inferred = report.get("inferred", {})
    print("Detected values from analyzer:")
    for key in ("entrypoint", "runtime", "framework", "dependencies", "env_vars", "services"):
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


def _prompt_yes_no(prompt: str, default: bool) -> bool:
    default_str = "y" if default else "n"
    value = _prompt_with_default(prompt, default_str).strip().lower()
    if value in {"y", "yes"}:
        return True
    if value in {"n", "no"}:
        return False
    return default


def _map_service_type(raw_type: str) -> str:
    lowered = raw_type.strip().lower()
    mapping = {
        "http": "api",
        "https": "api",
        "api": "api",
        "http-api": "api",
        "postgres": "database",
        "postgresql": "database",
        "database": "database",
        "redis": "database",
        "vector-db": "vector-db",
        "mcp-server": "mcp-server",
        "local-process": "local-process",
        "process": "local-process",
    }
    return mapping.get(lowered, "api")


def _normalize_inferred_services(services_value: Any) -> list[dict[str, Any]]:
    if not isinstance(services_value, list):
        return []

    normalized: list[dict[str, Any]] = []
    # Normalize analyzer-specific payloads to manifest-valid service objects.
    for index, service in enumerate(services_value, start=1):
        if not isinstance(service, dict):
            continue
        service_type = _map_service_type(str(service.get("type", "api")))
        endpoint = service.get("endpoint") if isinstance(service.get("endpoint"), str) else None
        service_name = f"service-{index}"
        if endpoint:
            parsed = urlsplit(endpoint)
            if parsed.hostname:
                service_name = parsed.hostname.replace(".", "-")

        normalized_service: dict[str, Any] = {
            "name": service_name,
            "type": service_type,
        }
        if service_type == "api" and endpoint:
            normalized_service["health_check"] = {
                "method": "http",
                "url": endpoint,
            }
        normalized.append(normalized_service)

    return normalized


def _prompt_services(default_services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw = _prompt_with_default(
        "Provide services (comma-separated service types, blank for none): ",
        "",
    )
    if not raw.strip():
        return default_services

    services: list[dict[str, Any]] = []
    for index, token in enumerate(raw.split(","), start=1):
        cleaned = token.strip()
        if not cleaned:
            continue
        services.append(
            {
                "name": f"service-{index}",
                "type": _map_service_type(cleaned),
            }
        )
    return services


def _prompt_permissions() -> dict[str, Any]:
    read_only = _prompt_yes_no("permissions.read_only? [Y/n]: ", True)
    allow_write = _prompt_yes_no("permissions.allow_write? [y/N]: ", False)
    allow_create = _prompt_yes_no("permissions.allow_create? [y/N]: ", False)
    allowed_paths_raw = _prompt_with_default(
        "permissions.allowed_paths (comma-separated, blank for none): ",
        "",
    )
    allowed_paths = [value.strip() for value in allowed_paths_raw.split(",") if value.strip()]
    return {
        "read_only": read_only,
        "allow_write": allow_write,
        "allow_create": allow_create,
        "allowed_paths": allowed_paths,
    }


def _extract_entrypoint_from_manifest(manifest_text: str) -> str | None:
    for line in manifest_text.splitlines():
        if line.startswith("entrypoint:"):
            value = line.split(":", 1)[1].strip()
            return value or None
    return None


def _replace_manifest_entrypoint(manifest_text: str, new_entrypoint: str) -> str:
    lines = manifest_text.splitlines()
    replaced: list[str] = []
    for line in lines:
        if line.startswith("entrypoint:"):
            replaced.append(f"entrypoint: {new_entrypoint}")
        else:
            replaced.append(line)
    return "\n".join(replaced) + "\n"


def _assess_entrypoint_contract(target_path: Path, entrypoint: str | None) -> str | None:
    if not entrypoint:
        return "Entrypoint is missing in generated manifest values."

    entrypoint_path = (target_path / entrypoint).resolve()
    if not entrypoint_path.exists():
        return f"Entrypoint '{entrypoint}' does not exist in target project."
    if entrypoint_path.suffix != ".py":
        return f"Entrypoint '{entrypoint}' is not a Python file."

    try:
        source = entrypoint_path.read_text(encoding="utf-8")
    except OSError:
        return f"Entrypoint '{entrypoint}' could not be inspected for compatibility."

    # This is intentionally heuristic and warning-only for migration safety.
    has_main_guard = "__name__" in source and "__main__" in source
    has_sys_argv = "sys.argv" in source
    if has_main_guard and has_sys_argv:
        return None

    return (
        f"Entrypoint '{entrypoint}' may not follow kinnoo one-shot CLI contract "
        "(expected __main__ guard and sys.argv input handling)."
    )


def _generate_entrypoint_wrapper(target_path: Path, original_entrypoint: str) -> str:
    wrapper_name = "kinnoo_wrapper.py"
    wrapper_path = target_path / wrapper_name
    if wrapper_path.exists():
        raise FileExistsError(
            "Optional wrapper generation aborted: kinnoo_wrapper.py already exists."
        )

    # Wrapper forwards argv and exit code so legacy scripts remain runnable.
    wrapper_source = (
        "import subprocess\n"
        "import sys\n"
        "from pathlib import Path\n\n"
        "if __name__ == '__main__':\n"
        f"    target = Path(__file__).with_name({original_entrypoint!r})\n"
        "    result = subprocess.run([sys.executable, str(target), *sys.argv[1:]])\n"
        "    raise SystemExit(result.returncode)\n"
    )
    wrapper_path.write_text(wrapper_source, encoding="utf-8")
    return wrapper_name


def _build_manifest_from_analysis(target_path: Path, report: dict[str, Any]) -> str:
    inferred = report.get("inferred", {})

    name = target_path.name.replace("_", "-").lower() or "imported-agent"
    entrypoint = inferred.get("entrypoint") or "run.py"

    runtime = inferred.get("runtime") if isinstance(inferred.get("runtime"), dict) else {}
    runtime_language = runtime.get("language") or "python"
    runtime_version = runtime.get("version") or ">=3.10"
    runtime_type = runtime.get("type")

    framework = inferred.get("framework")
    dependencies = inferred.get("dependencies") if isinstance(inferred.get("dependencies"), list) else []
    env_vars = inferred.get("env_vars") if isinstance(inferred.get("env_vars"), list) else []
    services = _normalize_inferred_services(inferred.get("services"))
    permissions: dict[str, Any] | None = None

    if _should_prompt_field(report, "entrypoint", entrypoint):
        entrypoint = _prompt_with_default("Provide value for entrypoint [run.py]: ", "run.py")

    if _should_prompt_field(report, "runtime", runtime_type):
        runtime_type = _prompt_with_default("Provide value for runtime.type [one-shot]: ", "one-shot")
    elif runtime_type is None:
        runtime_type = "one-shot"

    if _should_prompt_field(report, "framework", framework):
        framework_input = _prompt_with_default("Provide value for framework (optional): ", "")
        framework = framework_input or None

    if _should_prompt_field(report, "services", services):
        services = _prompt_services(services)

    runtime_prompt_needed = _should_prompt_field(report, "runtime", runtime.get("type"))
    if runtime_type == "mcp-server" and runtime_prompt_needed:
        if _prompt_yes_no("Configure permissions for mcp-server? [y/N]: ", False):
            permissions = _prompt_permissions()

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

    if services:
        manifest_lines.append("services:")
        for service in services:
            manifest_lines.append(f"  - name: {service['name']}")
            manifest_lines.append(f"    type: {service['type']}")
            health_check = service.get("health_check")
            if isinstance(health_check, dict):
                method = health_check.get("method")
                if method:
                    manifest_lines.append("    health_check:")
                    manifest_lines.append(f"      method: {method}")
                    if method == "http" and health_check.get("url"):
                        manifest_lines.append(f"      url: {health_check['url']}")

    if permissions:
        manifest_lines.append("permissions:")
        manifest_lines.append(f"  read_only: {str(permissions['read_only']).lower()}")
        manifest_lines.append(f"  allow_write: {str(permissions['allow_write']).lower()}")
        manifest_lines.append(f"  allow_create: {str(permissions['allow_create']).lower()}")
        manifest_lines.append("  allowed_paths:")
        for path in permissions["allowed_paths"]:
            manifest_lines.append(f"    - {path}")

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
    manifest_path = target_path / "kinnoo.yaml"
    generated_wrapper_path: Path | None = None

    if not target_path.exists():
        print(f"Error: import target does not exist: {target_path}")
        return 1

    if not target_path.is_dir():
        print(f"Error: import target must be a directory: {target_path}")
        return 1

    try:
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
        selected_entrypoint = _extract_entrypoint_from_manifest(manifest_text)
        entrypoint_warning = _assess_entrypoint_contract(target_path, selected_entrypoint)
        if entrypoint_warning:
            print(f"Entrypoint compatibility warning: {entrypoint_warning}")
            if _prompt_yes_no("Generate optional wrapper entrypoint bridge? [y/N]: ", False):
                if not selected_entrypoint:
                    print("Error: cannot generate wrapper without a valid entrypoint.")
                    return 1
                try:
                    wrapper_entrypoint = _generate_entrypoint_wrapper(target_path, selected_entrypoint)
                    generated_wrapper_path = target_path / wrapper_entrypoint
                except Exception as exc:
                    print(f"Error: optional wrapper generation failed: {exc}")
                    return 1
                manifest_text = _replace_manifest_entrypoint(manifest_text, wrapper_entrypoint)
    except ImportWizardInterrupted:
        if manifest_path.exists():
            manifest_path.unlink()
        if generated_wrapper_path and generated_wrapper_path.exists():
            generated_wrapper_path.unlink()
        print("Import interrupted (Ctrl+C/EOF). No partial artifacts were left behind.")
        return 1

    try:
        _write_manifest_in_place(target_path, manifest_text)
    except FileExistsError as exc:
        if generated_wrapper_path and generated_wrapper_path.exists():
            generated_wrapper_path.unlink()
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        if generated_wrapper_path and generated_wrapper_path.exists():
            generated_wrapper_path.unlink()
        print(f"Error: import failed and rolled back partial artifacts: {exc}")
        return 1

    print(f"Imported project in-place: {target_path}")
    return 0
