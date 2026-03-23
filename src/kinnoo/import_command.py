"""Import command surface for in-place onboarding workflows."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

try:
    from kinnoo.analyzer import analyze_project, infer_openclaw_project_hints
except ImportError:
    from .analyzer import analyze_project, infer_openclaw_project_hints

try:
    from kinnoo.validator import validate as validate_manifest
except ImportError:
    from .validator import validate as validate_manifest

try:
    from kinnoo.terminal_colors import style_text
except ImportError:
    from .terminal_colors import style_text


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


class PromptSession:
    """Track wizard input behavior to support automation-safe defaults."""

    def __init__(self) -> None:
        self.answers_received = 0
        self.non_interactive = not os.isatty(0)


_GITHUB_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def is_github_url(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    return _GITHUB_URL_RE.fullmatch(value.strip()) is not None


def github_repo_dir_name(url: str) -> str:
    match = _GITHUB_URL_RE.fullmatch(url.strip())
    if match is None:
        raise ValueError(f"Not a supported GitHub URL: {url}")

    repo_name = match.group("repo")
    if repo_name.lower().endswith(".git"):
        repo_name = repo_name[:-4]
    return repo_name


def clone_github_repo(url: str, destination: Path) -> tuple[bool, str]:
    git_executable = shutil.which("git")
    if git_executable is None:
        return False, "git is not installed or not available on PATH"

    result = subprocess.run(
        [git_executable, "clone", "--depth", "1", url, str(destination)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, ""

    combined = (result.stderr or result.stdout or "").strip()
    lowered = combined.lower()
    if "repository not found" in lowered or "not found" in lowered:
        return False, "repository URL not found or not accessible"
    if "authentication" in lowered or "permission denied" in lowered or "could not read" in lowered:
        return False, "authentication/credentials error while cloning repository"
    return False, combined or "git clone failed"


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


def _prompt_with_default(prompt: str, default: str, session: PromptSession | None = None) -> str:
    """Read a prompt value and raise when wizard interaction is interrupted."""
    try:
        value = input(prompt)
    except EOFError as exc:
        # In non-interactive automation, allow default-driven progression.
        if session and session.non_interactive:
            return default
        raise ImportWizardInterrupted("EOF") from exc
    except KeyboardInterrupt as exc:
        raise ImportWizardInterrupted("CTRL_C") from exc
    if session:
        session.answers_received += 1
    value = value.strip()
    return value if value else default


def _show_detected_values(report: dict[str, Any]) -> None:
    inferred = report.get("inferred", {})
    confidence = report.get("confidence", {})
    print(style_text("Detected values from analyzer:", color="cyan", bold=True))
    for key in ("entrypoint", "runtime", "framework", "model", "dependencies", "inputs", "outputs", "env_vars", "services"):
        print(f"  - {key}: {inferred.get(key)}")

    framework_confidence = confidence.get("framework")
    if isinstance(framework_confidence, dict):
        score = framework_confidence.get("score", 0.0)
        evidence = framework_confidence.get("evidence", "")
        print("Framework confidence metadata:")
        print(f"  - score: {score:.2f}" if isinstance(score, (int, float)) else f"  - score: {score}")
        if isinstance(evidence, str) and evidence:
            print(f"  - evidence: {evidence}")


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
    if isinstance(current_value, list) and not current_value:
        # Empty inferred list means "none detected" and should not force prompts.
        return False
    return _get_confidence(report, field_name) < 0.6


def _prompt_yes_no(prompt: str, default: bool, session: PromptSession | None = None) -> bool:
    default_str = "y" if default else "n"
    value = _prompt_with_default(prompt, default_str, session=session).strip().lower()
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


def _prompt_services(default_services: list[dict[str, Any]], session: PromptSession | None = None) -> list[dict[str, Any]]:
    raw = _prompt_with_default(
        "Provide services (comma-separated service types, blank for none): ",
        "",
        session=session,
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


def _prompt_permissions(session: PromptSession | None = None) -> dict[str, Any]:
    read_only = _prompt_yes_no("permissions.read_only? [Y/n]: ", True, session=session)
    allow_write = _prompt_yes_no("permissions.allow_write? [y/N]: ", False, session=session)
    allow_create = _prompt_yes_no("permissions.allow_create? [y/N]: ", False, session=session)
    allowed_paths_raw = _prompt_with_default(
        "permissions.allowed_paths (comma-separated, blank for none): ",
        "",
        session=session,
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


def _load_wrapper_template(template_name: str) -> str:
    template_path = Path(__file__).resolve().parent / "wrapper_templates" / template_name
    return template_path.read_text(encoding="utf-8")


def _render_wrapper_template(template_text: str, agent_module: str, agent_class: str) -> str:
    return (
        template_text
        .replace("{{agent_module}}", agent_module)
        .replace("{{agent_class}}", agent_class)
    )


def _generate_class_wrapper_entrypoint(
    target_path: Path,
    *,
    framework: str | None,
    agent_module: str,
    agent_class: str,
    force: bool,
) -> str:
    wrapper_name = "run.py"
    wrapper_path = target_path / wrapper_name
    if wrapper_path.exists() and not force:
        raise FileExistsError(
            "Class-wrapper generation aborted: run.py already exists. Use --force to overwrite."
        )

    template_name = "langchain_wrapper.py.j2"
    if framework == "openai-agents":
        template_name = "openai_agents_wrapper.py.j2"

    template_text = _load_wrapper_template(template_name)
    wrapper_source = _render_wrapper_template(template_text, agent_module, agent_class)
    wrapper_path.write_text(wrapper_source, encoding="utf-8")
    return wrapper_name


def _build_manifest_from_analysis(
    target_path: Path,
    report: dict[str, Any],
    *,
    session: PromptSession | None = None,
) -> str:
    inferred = report.get("inferred", {})

    name = target_path.name.replace("_", "-").lower() or "imported-agent"
    entrypoint = inferred.get("entrypoint") or "run.py"

    runtime = inferred.get("runtime") if isinstance(inferred.get("runtime"), dict) else {}
    runtime_language = runtime.get("language") or "python"
    runtime_version = runtime.get("version") or ">=3.10"
    runtime_type = runtime.get("type")
    runtime_package_manager = runtime.get("package_manager") if isinstance(runtime.get("package_manager"), str) else None

    framework = inferred.get("framework")
    model = inferred.get("model") if isinstance(inferred.get("model"), str) else None
    dependencies = inferred.get("dependencies") if isinstance(inferred.get("dependencies"), list) else []
    env_vars = inferred.get("env_vars") if isinstance(inferred.get("env_vars"), list) else []
    services = _normalize_inferred_services(inferred.get("services"))
    permissions: dict[str, Any] | None = None
    inferred_input_type = inferred.get("inputs") if isinstance(inferred.get("inputs"), str) else "string"
    inferred_output_type = inferred.get("outputs") if isinstance(inferred.get("outputs"), str) else "string"
    allowed_io_types = {"text", "string", "file", "json"}
    if inferred_input_type not in allowed_io_types:
        inferred_input_type = "string"
    if inferred_output_type not in allowed_io_types:
        inferred_output_type = "string"

    # If analyzer inferred an entrypoint and user confirmed detected values,
    # keep it without re-prompting even when confidence is low.
    if not isinstance(inferred.get("entrypoint"), str) or not str(inferred.get("entrypoint")).strip():
        entrypoint = _prompt_with_default("Provide value for entrypoint [run.py]: ", "run.py", session=session)

    if _should_prompt_field(report, "runtime", runtime_type):
        runtime_type = _prompt_with_default(
            "Provide value for runtime.type [one-shot]: ",
            "one-shot",
            session=session,
        )
    elif runtime_type is None:
        runtime_type = "one-shot"

    if _should_prompt_field(report, "framework", framework):
        framework_input = _prompt_with_default(
            "Provide value for framework (optional): ",
            "",
            session=session,
        )
        framework = framework_input or None

    inferred_skills: list[str] = []
    inferred_state_dirs: list[str] = []
    if framework == "openclaw":
        openclaw_hints = infer_openclaw_project_hints(target_path)
        hinted_runtime = openclaw_hints.get("runtime")
        if isinstance(hinted_runtime, dict):
            runtime_language = str(hinted_runtime.get("language", runtime_language))
            runtime_type = str(hinted_runtime.get("type", runtime_type or "daemon"))
            runtime_version = str(hinted_runtime.get("version", runtime_version))
            package_manager_hint = hinted_runtime.get("package_manager")
            if isinstance(package_manager_hint, str) and package_manager_hint:
                runtime_package_manager = package_manager_hint

        raw_skills = openclaw_hints.get("skills")
        if isinstance(raw_skills, list):
            inferred_skills = [value for value in raw_skills if isinstance(value, str) and value.strip()]

        raw_state_dirs = openclaw_hints.get("state_dirs")
        if isinstance(raw_state_dirs, list):
            inferred_state_dirs = [value for value in raw_state_dirs if isinstance(value, str) and value.strip()]

    if _should_prompt_field(report, "services", services):
        services = _prompt_services(services, session=session)

    runtime_prompt_needed = _should_prompt_field(report, "runtime", runtime.get("type"))
    if runtime_type == "mcp-server" and runtime_prompt_needed:
        if _prompt_yes_no("Configure permissions for mcp-server? [y/N]: ", False, session=session):
            permissions = _prompt_permissions(session=session)

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
        f"  type: {inferred_input_type}",
        "outputs:",
        f"  type: {inferred_output_type}",
    ]

    if runtime_package_manager:
        manifest_lines.insert(6, f"  package_manager: {runtime_package_manager}")

    if framework:
        manifest_lines.append(f"framework: {framework}")

    if model and model.strip():
        manifest_lines.append(f"model: {model.strip()}")

    if inferred_skills:
        manifest_lines.append("skills:")
        for skill_path in inferred_skills:
            manifest_lines.append(f"  - {skill_path}")

    if inferred_state_dirs:
        manifest_lines.append("state_dirs:")
        for state_dir in inferred_state_dirs:
            manifest_lines.append(f"  - {state_dir}")

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


def _write_manifest_in_place(target_path: Path, manifest_text: str, *, force: bool = False) -> None:
    manifest_path = target_path / "kinnoo.yaml"
    if manifest_path.exists() and not force:
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


def _normalize_dependency_list(raw_dependencies: Any) -> list[str]:
    """Normalize inferred dependency values to deterministic requirements lines."""
    if not isinstance(raw_dependencies, list):
        return []

    normalized: list[str] = []
    for value in raw_dependencies:
        if not isinstance(value, str):
            continue
        candidate = value.strip()
        if not candidate:
            continue
        normalized.append(candidate)

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(normalized))


def _attempt_uv_requirements_export(target_path: Path) -> tuple[bool, str | None]:
    """Try generating requirements text via uv export for Python projects."""
    if shutil.which("uv") is None:
        return False, "uv executable not found"

    command = [
        "uv",
        "export",
        "--directory",
        str(target_path),
        "--format",
        "requirements-txt",
        "--no-hashes",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "uv export failed").strip()
        return False, detail

    exported = result.stdout.strip()
    if exported:
        return True, exported + "\n"
    return True, ""


def _ensure_import_requirements_file(
    target_path: Path,
    *,
    inferred_dependencies: Any,
    runtime_language: str,
) -> bool:
    """Create requirements.txt for imported Python projects when missing.

    Returns True when a new requirements.txt file is created by this function.
    """
    requirements_path = target_path / "requirements.txt"
    if requirements_path.exists():
        return False

    if runtime_language.strip().lower() != "python":
        return False

    dependencies = _normalize_dependency_list(inferred_dependencies)
    if dependencies:
        requirements_path.write_text("\n".join(dependencies) + "\n", encoding="utf-8")
        print("Generated requirements.txt from analyzer-detected dependencies.")
        return True

    exported_ok, exported_text_or_error = _attempt_uv_requirements_export(target_path)
    if exported_ok:
        requirements_path.write_text(exported_text_or_error or "", encoding="utf-8")
        print("Generated requirements.txt via uv export.")
        return True

    requirements_path.write_text("", encoding="utf-8")
    print(
        "Generated empty requirements.txt (no Python dependencies detected). "
        f"uv export was unavailable or failed: {exported_text_or_error}"
    )
    return True


def _collect_unresolved_todo_guidance(
    report: dict[str, Any],
    entrypoint_warning: str | None,
) -> list[str]:
    guidance: list[str] = []

    if _get_confidence(report, "entrypoint") < 0.6:
        guidance.append("Verify 'entrypoint' points to an existing executable script in the project root.")

    if _get_confidence(report, "runtime") < 0.6:
        guidance.append("Verify runtime fields (runtime.type, runtime.language, runtime.version) before first run.")

    inferred_framework = report.get("inferred", {}).get("framework")
    framework_confidence = _get_confidence(report, "framework")
    if inferred_framework is None and framework_confidence > 0.0:
        guidance.append(
            "Framework inference is ambiguous; set 'framework' explicitly if this project depends on one."
        )

    if entrypoint_warning:
        guidance.append(entrypoint_warning)

    # Preserve deterministic order while removing duplicates.
    return list(dict.fromkeys(guidance))


def _print_manifest_validation_and_guidance(
    manifest_path: Path,
    report: dict[str, Any],
    entrypoint_warning: str | None,
) -> None:
    is_valid, errors = validate_manifest(str(manifest_path))
    if is_valid:
        print(style_text("Generated manifest validation: PASS", color="green", bold=True))
    else:
        print(style_text("Generated manifest validation: WARNING", color="yellow", bold=True))
        for error in errors:
            print(f"  - {error}")

    unresolved_guidance = _collect_unresolved_todo_guidance(report, entrypoint_warning)
    if is_valid and not unresolved_guidance:
        return

    print(style_text("TODO guidance:", color="yellow", bold=True))
    for item in unresolved_guidance:
        print(f"  - {item}")

    if not is_valid:
        print("  - Update kinnoo.yaml to resolve validation warnings before packaging or distribution.")


def import_agent(
    target_path_arg: str | None,
    import_path_arg: str | None = None,
    *,
    force: bool = False,
) -> int:
    """Import a project in-place by writing kinnoo.yaml safely into target root."""
    target_arg = target_path_arg
    if target_arg is None:
        target_arg = str(Path.cwd())

    if import_path_arg is not None and not is_github_url(target_arg):
        print(style_text("Error: import-path positional argument is only supported for GitHub URL imports.", color="red"))
        print("Usage: kinnoo import [target] [import-path] [--force]")
        return 1

    target_path: Path
    if is_github_url(target_arg):
        repo_url = target_arg.strip()
        if import_path_arg is None:
            destination = Path.cwd() / github_repo_dir_name(repo_url)
        else:
            destination = Path(import_path_arg).expanduser().resolve()

        if destination.exists():
            print(style_text(f"Error: import target directory already exists: {destination}", color="red"))
            return 1

        cloned, clone_error = clone_github_repo(repo_url, destination)
        if not cloned:
            print(style_text(
                "Error: failed to download/clone agent code from GitHub URL "
                f"'{repo_url}': {clone_error}"
            , color="red"))
            return 1

        target_path = destination
    else:
        target_path = _resolve_import_target(target_arg)

    manifest_path = target_path / "kinnoo.yaml"
    generated_wrapper_path: Path | None = None
    created_requirements_file = False

    if not target_path.exists():
        print(style_text(f"Error: import target does not exist: {target_path}", color="red"))
        return 1

    if not target_path.is_dir():
        print(style_text(f"Error: import target must be a directory: {target_path}", color="red"))
        return 1

    if manifest_path.exists() and not force:
        print(style_text(
            "Error: Import aborted: kinnoo.yaml already exists. "
            "Use --force to explicitly override and overwrite."
        , color="red"))
        return 1

    session = PromptSession()
    entrypoint_warning: str | None = None
    report_for_manifest: dict[str, Any] | None = None

    try:
        report = analyze_project(target_path).as_dict()
        report_for_manifest = report
        _show_detected_values(report)

        warning_messages = report.get("warnings", [])
        if warning_messages:
            print(style_text("Analyzer warnings:", color="yellow", bold=True))
            for warning in warning_messages:
                print(f"  - {warning}")

        confirmed = _prompt_with_default(
            "Proceed with detected values? [Y/n]: ",
            "y",
            session=session,
        ).lower()
        if confirmed not in {"y", "yes"}:
            print("Import cancelled by user.")
            return 1

        inferred = report.get("inferred", {})
        detected_entrypoint = inferred.get("entrypoint")
        if isinstance(detected_entrypoint, dict) and detected_entrypoint.get("entrypoint_type") == "class":
            agent_class = detected_entrypoint.get("agent_class")
            agent_module = detected_entrypoint.get("agent_module")
            if isinstance(agent_class, str) and isinstance(agent_module, str):
                if _prompt_yes_no(
                    "Generate class-based run.py wrapper entrypoint? [y/N]: ",
                    False,
                    session=session,
                ):
                    try:
                        wrapper_entrypoint = _generate_class_wrapper_entrypoint(
                            target_path,
                            framework=inferred.get("framework") if isinstance(inferred.get("framework"), str) else None,
                            agent_module=agent_module,
                            agent_class=agent_class,
                            force=force,
                        )
                        generated_wrapper_path = target_path / wrapper_entrypoint
                    except Exception as exc:
                        print(style_text(f"Error: class-wrapper generation failed: {exc}", color="red"))
                        return 1

                    manifest_inferred = dict(inferred)
                    manifest_inferred["entrypoint"] = wrapper_entrypoint
                    report_for_manifest = dict(report)
                    report_for_manifest["inferred"] = manifest_inferred

        manifest_text = _build_manifest_from_analysis(target_path, report_for_manifest or report, session=session)
        selected_entrypoint = _extract_entrypoint_from_manifest(manifest_text)
        entrypoint_warning = _assess_entrypoint_contract(target_path, selected_entrypoint)
        if entrypoint_warning:
            print(f"Entrypoint compatibility warning: {entrypoint_warning}")
            wrapper_eligible = "may not follow kinnoo one-shot CLI contract" in entrypoint_warning
            if wrapper_eligible and _prompt_yes_no(
                "Generate optional wrapper entrypoint bridge? [y/N]: ",
                False,
                session=session,
            ):
                if not selected_entrypoint:
                    print("Error: cannot generate wrapper without a valid entrypoint.")
                    return 1
                try:
                    wrapper_entrypoint = _generate_entrypoint_wrapper(target_path, selected_entrypoint)
                    generated_wrapper_path = target_path / wrapper_entrypoint
                except Exception as exc:
                    print(style_text(f"Error: optional wrapper generation failed: {exc}", color="red"))
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
        _write_manifest_in_place(target_path, manifest_text, force=force)

        inferred = report.get("inferred", {})
        runtime_info = inferred.get("runtime") if isinstance(inferred.get("runtime"), dict) else {}
        runtime_language = str(runtime_info.get("language") or "python")
        created_requirements_file = _ensure_import_requirements_file(
            target_path,
            inferred_dependencies=inferred.get("dependencies"),
            runtime_language=runtime_language,
        )
    except FileExistsError as exc:
        if generated_wrapper_path and generated_wrapper_path.exists():
            generated_wrapper_path.unlink()
        print(style_text(f"Error: {exc}", color="red"))
        return 1
    except Exception as exc:
        if created_requirements_file:
            requirements_path = target_path / "requirements.txt"
            if requirements_path.exists():
                requirements_path.unlink()
        if manifest_path.exists():
            manifest_path.unlink()
        if generated_wrapper_path and generated_wrapper_path.exists():
            generated_wrapper_path.unlink()
        print(style_text(f"Error: import failed and rolled back partial artifacts: {exc}", color="red"))
        return 1

    _print_manifest_validation_and_guidance(
        manifest_path,
        report,
        entrypoint_warning,
    )

    print(style_text(f"Imported project in-place: {target_path}", color="green", bold=True))
    return 0
