from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path
import os
import getpass
from typing import Iterable
import re
import json
import signal
import time
import threading
from datetime import datetime, timezone

import yaml

from .health_check import (
    DaemonLifecycleResult,
    HealthCheckResult,
    check_node_package_manager_availability,
    check_node_runtime_constraint,
    classify_daemon_lifecycle_state,
    run_service_health_check,
)
from .schema import SUPPORTED_NODE_PACKAGE_MANAGERS, normalize_env_vars
from .sandbox import evaluate_sandbox_permissions
from .install_trace import write_violation_event
from .logging_utils import emit_violation_event_diagnostic
from .runtime_monitor import RuntimeMonitor
from .runtime_monitor import resolve_violation_enforcement
from .supervisor import (
    build_daemon_state_payload,
    clear_daemon_state,
    daemon_pid_is_running,
    daemon_log_path,
    daemon_state_path,
    infer_readiness_config,
    shutdown_server_with_report,
    shutdown_server,
    start_server,
    stop_daemon_pid,
    stream_output,
    wait_until_ready,
    write_daemon_state,
)
from .validator import validate


def _redact_secrets(text: str, secret_values: Iterable[str]) -> str:
    redacted_text = text
    for secret_value in secret_values:
        if not secret_value:
            continue
        redacted_text = redacted_text.replace(secret_value, "[REDACTED]")
    return redacted_text


def _print_safe_error(message: str, secret_values: Iterable[str] | None = None) -> None:
    output = message
    if secret_values is not None:
        output = _redact_secrets(message, secret_values)
    print(output, file=sys.stderr)


def _contains_forbidden_value(text: str, forbidden_values: Iterable[str]) -> bool:
    for forbidden_value in forbidden_values:
        if not forbidden_value:
            continue
        if forbidden_value in text:
            return True
    return False


def _load_agent_dotenv(dotenv_path: Path) -> dict[str, str]:
    """Load key/value pairs from an agent-local .env file.

    Parsing is intentionally conservative and tolerant of malformed lines:
    - blank lines and comment lines are ignored,
    - `export KEY=VALUE` is supported,
    - lines without `=` are ignored.
    """
    values: dict[str, str] = {}
    if not dotenv_path.exists():
        return values

    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return values

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = value.strip()

    return values


def _emit_preflight_line(passed: bool, message: str) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"- [{status}] {message}")


def _load_declared_services(manifest: dict | None) -> list[dict[str, object]]:
    if not isinstance(manifest, dict):
        return []

    declared_services = manifest.get("services")
    if not isinstance(declared_services, list):
        return []

    normalized_services: list[dict[str, object]] = []
    for service_entry in declared_services:
        if isinstance(service_entry, dict):
            normalized_services.append(service_entry)
    return normalized_services


def _run_service_checks(manifest: dict | None) -> list[HealthCheckResult]:
    results: list[HealthCheckResult] = []
    for declared_service in _load_declared_services(manifest):
        results.append(run_service_health_check(declared_service))
    return results


def _render_service_check_for_preflight(result: HealthCheckResult) -> None:
    detail = (
        f"service '{result.service_name}' (type: {result.service_type}, method: {result.method}) "
        f"{result.message}"
    )
    _emit_preflight_line(result.healthy, detail)
    if not result.healthy:
        print(f"  - Guidance: {result.guidance}")


def _render_service_check_for_run(result: HealthCheckResult) -> None:
    status = "PASS" if result.healthy else "FAIL"
    detail = (
        f"service '{result.service_name}' (type: {result.service_type}, method: {result.method}) "
        f"{result.message}"
    )
    print(f"[kinnoo] service check [{status}] {detail}", flush=True)
    if not result.healthy:
        print(f"[kinnoo] guidance: {result.guidance}", flush=True)


def _parse_runtime_version(value: str) -> tuple[int, ...] | None:
    if not value:
        return None

    if not re.fullmatch(r"\d+(?:\.\d+)*", value):
        return None

    return tuple(int(part) for part in value.split("."))


def _compare_versions(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    max_len = max(len(left), len(right))
    padded_left = left + (0,) * (max_len - len(left))
    padded_right = right + (0,) * (max_len - len(right))
    if padded_left < padded_right:
        return -1
    if padded_left > padded_right:
        return 1
    return 0


def _runtime_constraint_satisfied(constraint: str, current_version: tuple[int, ...]) -> bool:
    normalized_constraint = constraint.strip()
    if not normalized_constraint:
        return False

    operator = "=="
    value = normalized_constraint
    for candidate in (">=", "<=", "==", ">", "<"):
        if normalized_constraint.startswith(candidate):
            operator = candidate
            value = normalized_constraint[len(candidate):].strip()
            break

    required_version = _parse_runtime_version(value)
    if required_version is None:
        return False

    comparison = _compare_versions(current_version, required_version)
    if operator == "==":
        return comparison == 0
    if operator == ">=":
        return comparison >= 0
    if operator == "<=":
        return comparison <= 0
    if operator == ">":
        return comparison > 0
    if operator == "<":
        return comparison < 0
    return False


def _check_runtime_version_constraint(runtime_constraint: str) -> tuple[bool, str]:
    normalized = runtime_constraint.strip()
    current_version = (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    current_label = ".".join(str(part) for part in current_version)

    if not normalized:
        return False, "runtime.version constraint is empty"

    constraints = [segment.strip() for segment in normalized.split(",") if segment.strip()]
    if not constraints:
        return False, "runtime.version constraint is empty"

    invalid_constraints: list[str] = []
    for constraint in constraints:
        if not _runtime_constraint_satisfied(constraint, current_version):
            invalid_constraints.append(constraint)

    if invalid_constraints:
        constraint_label = ", ".join(constraints)
        return (
            False,
            (
                "runtime version check failed: "
                f"current Python {current_label} does not satisfy runtime.version '{constraint_label}'"
            ),
        )

    return (
        True,
        (
            "runtime version check passed: "
            f"current Python {current_label} satisfies runtime.version '{normalized}'"
        ),
    )


def _check_preflight_env_vars(manifest: dict, agent_dir: Path) -> tuple[bool, str]:
    declared_env_vars = normalize_env_vars(manifest.get("env_vars"))
    if not declared_env_vars:
        return True, "env vars check passed: no env_vars declared"

    dotenv_values = _load_agent_dotenv(agent_dir / ".env")
    missing_env_vars: list[str] = []
    for env_var_name in declared_env_vars:
        if os.environ.get(env_var_name) is not None:
            continue
        if dotenv_values.get(env_var_name) is not None:
            continue
        missing_env_vars.append(env_var_name)

    if missing_env_vars:
        # [agent] SECURITY INVARIANT: only env var NAMES, never values
        missing_label = ", ".join(missing_env_vars)
        return False, f"env vars check failed: unresolved env vars [{missing_label}]"

    # [agent] SECURITY INVARIANT: only env var NAMES, never values
    declared_label = ", ".join(declared_env_vars)
    return True, f"env vars check passed: resolved env vars [{declared_label}]"


def _extract_dependency_names(requirements_path: Path) -> list[str]:
    if not requirements_path.exists():
        return []

    dependency_names: list[str] = []
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-", "--")):
            continue
        normalized = line.split(";", 1)[0].strip()
        if not normalized:
            continue
        if "@" in normalized:
            normalized = normalized.split("@", 1)[0].strip()

        package_name = re.split(r"[<>=!~\[\s]", normalized, maxsplit=1)[0].strip()
        if package_name:
            dependency_names.append(package_name)

    unique_dependency_names: list[str] = []
    seen: set[str] = set()
    for dependency_name in dependency_names:
        key = dependency_name.lower()
        if key in seen:
            continue
        unique_dependency_names.append(dependency_name)
        seen.add(key)
    return unique_dependency_names


def _check_preflight_entrypoint(manifest: dict, agent_dir: Path) -> tuple[bool, str]:
    entrypoint = manifest.get("entrypoint")
    if not isinstance(entrypoint, str) or not entrypoint.strip():
        return False, "entrypoint check failed: manifest entrypoint is missing or empty"

    entrypoint_path = agent_dir / entrypoint
    if not entrypoint_path.exists():
        return False, f"entrypoint check failed: entrypoint file not found: {entrypoint_path}"
    if not entrypoint_path.is_file():
        return False, f"entrypoint check failed: entrypoint path is not a file: {entrypoint_path}"
    if not os.access(entrypoint_path, os.R_OK):
        return False, f"entrypoint check failed: entrypoint file is not readable: {entrypoint_path}"

    return True, f"entrypoint check passed: readable entrypoint file {entrypoint_path}"


def _resolve_venv_pip(venv_dir: Path) -> Path | None:
    pip_candidates = [
        venv_dir / "bin" / "pip",
        venv_dir / "Scripts" / "pip.exe",
    ]
    for pip_candidate in pip_candidates:
        if pip_candidate.exists():
            return pip_candidate
    return None


def _check_preflight_dependencies(manifest: dict, agent_dir: Path) -> tuple[bool, str]:
    del manifest
    requirements_path = agent_dir / "requirements.txt"
    dependency_names = _extract_dependency_names(requirements_path)
    if not dependency_names:
        return True, "dependency readiness check passed: no installable dependencies declared"

    venv_dir = agent_dir / ".venv"
    if not venv_dir.exists() or not venv_dir.is_dir():
        return False, f"dependency readiness check failed: virtual environment not found at {venv_dir}"

    pip_exe = _resolve_venv_pip(venv_dir)
    if pip_exe is None:
        return False, f"dependency readiness check failed: pip executable not found in {venv_dir}"

    missing_dependencies: list[str] = []
    for dependency_name in dependency_names:
        result = subprocess.run(
            [str(pip_exe), "show", dependency_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            missing_dependencies.append(dependency_name)

    if missing_dependencies:
        missing_label = ", ".join(missing_dependencies)
        return False, f"dependency readiness check failed: missing packages [{missing_label}]"

    dependency_label = ", ".join(dependency_names)
    return True, f"dependency readiness check passed: installed packages [{dependency_label}]"


def _manifest_inputs_required(manifest: dict) -> bool:
    inputs_section = manifest.get("inputs")
    if not isinstance(inputs_section, dict):
        return True
    required_value = inputs_section.get("required")
    if isinstance(required_value, bool):
        return required_value
    return True


def _manifest_declares_json_input(manifest: dict) -> bool:
    inputs_section = manifest.get("inputs")
    if not isinstance(inputs_section, dict):
        return False

    declared_type = inputs_section.get("type")
    if isinstance(declared_type, str):
        return declared_type.strip().lower() == "json"
    if isinstance(declared_type, list):
        return any(
            isinstance(item, str) and item.strip().lower() == "json"
            for item in declared_type
        )
    return False


def _manifest_declares_json_output(manifest: dict) -> bool:
    outputs_section = manifest.get("outputs")
    if not isinstance(outputs_section, dict):
        return False

    declared_type = outputs_section.get("type")
    if isinstance(declared_type, str):
        return declared_type.strip().lower() == "json"
    if isinstance(declared_type, list):
        return any(
            isinstance(item, str) and item.strip().lower() == "json"
            for item in declared_type
        )
    return False


def _manifest_declared_io_types(manifest: dict, section_name: str) -> list[str]:
    section = manifest.get(section_name)
    if not isinstance(section, dict):
        return []

    declared_type = section.get("type")
    if isinstance(declared_type, str):
        value = declared_type.strip().lower()
        return [value] if value else []
    if isinstance(declared_type, list):
        normalized: list[str] = []
        for item in declared_type:
            if not isinstance(item, str):
                continue
            value = item.strip().lower()
            if value and value not in normalized:
                normalized.append(value)
        return normalized
    return []


def _stream_and_capture_process_output(process: subprocess.Popen) -> tuple[str, str]:
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def _pump(stream, target_stream, chunks: list[str]) -> None:
        if stream is None:
            return
        for line in iter(stream.readline, ""):
            chunks.append(line)
            target_stream.write(line)
            target_stream.flush()
        stream.close()

    stdout_thread = threading.Thread(
        target=_pump,
        args=(process.stdout, sys.stdout, stdout_chunks),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_pump,
        args=(process.stderr, sys.stderr, stderr_chunks),
        daemon=True,
    )

    stdout_thread.start()
    stderr_thread.start()

    process.wait()
    stdout_thread.join()
    stderr_thread.join()

    return "".join(stdout_chunks), "".join(stderr_chunks)


def _load_json_payload_from_file(json_file_arg: str, secret_values: Iterable[str]) -> object:
    json_path = Path(json_file_arg).resolve()
    if not json_path.exists():
        raise ValueError(f"Error: JSON input file not found: {json_path}")
    if not json_path.is_file():
        raise ValueError(f"Error: JSON input path is not a file: {json_path}")

    try:
        raw_payload = json_path.read_text(encoding="utf-8")
    except Exception as error:
        raise ValueError(f"Error: Failed to read JSON input file '{json_path}': {error}") from error

    if _contains_forbidden_value(raw_payload, secret_values):
        raise ValueError("Error: JSON input file contains sensitive values that must not be echoed")

    try:
        return json.loads(raw_payload)
    except json.JSONDecodeError as error:
        raise ValueError(
            "Error: Invalid JSON in --json-file payload "
            f"at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error


def _resolve_effective_input_arg(
    *,
    manifest: dict,
    input_arg: str | None,
    json_input_arg: str | None,
    json_file_arg: str | None,
    secret_values: Iterable[str],
) -> str | None:
    if json_input_arg is not None and json_file_arg is not None:
        raise ValueError("Error: --json-input and --json-file are mutually exclusive")

    json_mode_selected = json_input_arg is not None or json_file_arg is not None
    if json_mode_selected and input_arg is not None:
        raise ValueError("Error: positional <input> cannot be used with --json-input or --json-file")

    if not json_mode_selected:
        return input_arg

    if not _manifest_declares_json_input(manifest):
        raise ValueError(
            "Error: JSON input mode requires manifest inputs.type to include 'json'"
        )

    payload: object
    if json_input_arg is not None:
        try:
            payload = json.loads(json_input_arg)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Error: Invalid JSON in --json-input payload "
                f"at line {error.lineno}, column {error.colno}: {error.msg}"
            ) from error
    else:
        assert json_file_arg is not None
        payload = _load_json_payload_from_file(json_file_arg, secret_values)

    # Canonical JSON string keeps subprocess contract deterministic across modes.
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _infer_pass_through_input_type(param_name: str) -> str:
    type_by_flag = {
        "-u": "url",
        "--url": "url",
        "-p": "file_path",
        "--path": "file_path",
        "-d": "file_path",
        "--data-path": "file_path",
        "-i": "id",
        "--id": "id",
        "-e": "string",
        "--text": "string",
    }
    return type_by_flag.get(param_name, "text")


def _build_pass_through_guard_inputs(pass_through_args: list[str]) -> list[tuple[str, str, str]]:
    inputs: list[tuple[str, str, str]] = []
    index = 0
    while index < len(pass_through_args):
        token = pass_through_args[index]
        if token.startswith("-") and index + 1 < len(pass_through_args):
            candidate_value = pass_through_args[index + 1]
            if not candidate_value.startswith("-"):
                inputs.append((token, candidate_value, _infer_pass_through_input_type(token)))
                index += 2
                continue

        if not token.startswith("-"):
            inputs.append((f"arg{index}", token, "text"))
        index += 1

    return inputs


def run_preflight(agent_dir_arg: str) -> int:
    """Run preflight-only checks without executing the agent entrypoint."""
    agent_dir = Path(agent_dir_arg).resolve()
    kinnoo_yaml = agent_dir / "kinnoo.yaml"

    print("Preflight checklist:")

    agent_dir_exists = agent_dir.exists() and agent_dir.is_dir()
    _emit_preflight_line(agent_dir_exists, f"agent directory exists: {agent_dir}")

    manifest_exists = kinnoo_yaml.exists()
    _emit_preflight_line(manifest_exists, f"manifest exists: {kinnoo_yaml}")

    manifest_valid = False
    manifest: dict | None = None
    if manifest_exists:
        manifest_valid, manifest_errors = validate(str(kinnoo_yaml))
        _emit_preflight_line(manifest_valid, "manifest validates against kinnoo schema")
        if not manifest_valid:
            for manifest_error in manifest_errors:
                print(f"  - {manifest_error}")
        else:
            with kinnoo_yaml.open("r", encoding="utf-8") as manifest_file:
                loaded_manifest = yaml.safe_load(manifest_file)
            if isinstance(loaded_manifest, dict):
                manifest = loaded_manifest

    runtime_language = "python"
    runtime_type = "one-shot"
    runtime_section: dict[str, object] = {}
    if isinstance(manifest, dict):
        candidate_runtime = manifest.get("runtime")
        if isinstance(candidate_runtime, dict):
            runtime_section = candidate_runtime
            runtime_language_value = runtime_section.get("language")
            if isinstance(runtime_language_value, str) and runtime_language_value.strip():
                runtime_language = runtime_language_value.strip().lower()
            runtime_type_value = runtime_section.get("type")
            if isinstance(runtime_type_value, str) and runtime_type_value.strip():
                runtime_type = runtime_type_value.strip().lower()

    runtime_constraint_ok = False
    runtime_message = "runtime version check failed: manifest validation prerequisite not met"
    env_vars_ok = False
    env_vars_message = "env vars check failed: manifest validation prerequisite not met"
    entrypoint_ok = False
    entrypoint_message = "entrypoint check failed: manifest validation prerequisite not met"
    dependencies_ok = False
    dependencies_message = "dependency readiness check failed: manifest validation prerequisite not met"
    if manifest_valid and manifest is not None:
        runtime_version_constraint = str(runtime_section.get("version", ""))
        if runtime_language == "nodejs":
            runtime_constraint_ok, runtime_message = check_node_runtime_constraint(runtime_version_constraint)
        else:
            runtime_constraint_ok, runtime_message = _check_runtime_version_constraint(runtime_version_constraint)

        env_vars_ok, env_vars_message = _check_preflight_env_vars(manifest, agent_dir)

        entrypoint_ok, entrypoint_message = _check_preflight_entrypoint(manifest, agent_dir)

        if runtime_language == "nodejs":
            package_manager_raw = runtime_section.get("package_manager")
            package_manager = "npm"
            if package_manager_raw is not None:
                if isinstance(package_manager_raw, str) and package_manager_raw.strip():
                    normalized_manager = package_manager_raw.strip().lower()
                    if normalized_manager in SUPPORTED_NODE_PACKAGE_MANAGERS:
                        package_manager = normalized_manager
                    else:
                        supported = ", ".join(SUPPORTED_NODE_PACKAGE_MANAGERS)
                        dependencies_ok = False
                        dependencies_message = (
                            "dependency readiness check failed: "
                            f"unsupported runtime.package_manager '{package_manager_raw}'. "
                            f"Supported values: {supported}"
                        )
                else:
                    dependencies_ok = False
                    dependencies_message = (
                        "dependency readiness check failed: "
                        "runtime.package_manager must be a non-empty string when provided"
                    )

            if dependencies_message == "dependency readiness check failed: manifest validation prerequisite not met":
                dependencies_ok, dependencies_message = check_node_package_manager_availability(package_manager)
        else:
            dependencies_ok, dependencies_message = _check_preflight_dependencies(manifest, agent_dir)

    _emit_preflight_line(runtime_constraint_ok, runtime_message)
    _emit_preflight_line(env_vars_ok, env_vars_message)
    _emit_preflight_line(entrypoint_ok, entrypoint_message)
    _emit_preflight_line(dependencies_ok, dependencies_message)

    io_contract_ok = False
    io_contract_message = "manifest I/O contract unavailable: manifest validation prerequisite not met"
    if manifest_valid and manifest is not None:
        input_types = _manifest_declared_io_types(manifest, "inputs")
        output_types = _manifest_declared_io_types(manifest, "outputs")
        input_label = ", ".join(input_types) if input_types else "(none)"
        output_label = ", ".join(output_types) if output_types else "(none)"

        contract_notes: list[str] = []
        if "json" in input_types:
            contract_notes.append("use --json-input or --json-file for structured input")
        if runtime_type != "mcp-server" and "json" in output_types:
            contract_notes.append("stdout must be valid JSON when outputs.type includes json")

        io_contract_message = (
            f"manifest I/O contract: inputs.type [{input_label}], outputs.type [{output_label}]"
        )
        if contract_notes:
            io_contract_message = f"{io_contract_message}; {'; '.join(contract_notes)}"
        io_contract_ok = True
    _emit_preflight_line(io_contract_ok, io_contract_message)

    service_results: list[HealthCheckResult] = []
    service_checks_ok = True
    if manifest_valid and manifest is not None:
        service_results = _run_service_checks(manifest)
        if service_results:
            print("Service health checks:")
            for service_result in service_results:
                _render_service_check_for_preflight(service_result)
            service_checks_ok = all(service_result.healthy for service_result in service_results)

    daemon_lifecycle_result: DaemonLifecycleResult | None = None
    daemon_state_ok = True
    if runtime_type == "daemon" and manifest_valid and manifest is not None:
        state_path = daemon_state_path(agent_dir)
        has_state_metadata = state_path.exists()
        process_running = False
        if has_state_metadata:
            try:
                state_payload = json.loads(state_path.read_text(encoding="utf-8"))
                pid_value = state_payload.get("pid") if isinstance(state_payload, dict) else None
                if isinstance(pid_value, int):
                    process_running = daemon_pid_is_running(pid_value)
            except Exception:
                process_running = False

        daemon_lifecycle_result = classify_daemon_lifecycle_state(
            has_state_metadata=has_state_metadata,
            process_running=process_running,
            service_results=service_results,
        )
        daemon_state_ok = daemon_lifecycle_result.healthy
        _emit_preflight_line(
            daemon_lifecycle_result.healthy,
            f"daemon lifecycle state [{daemon_lifecycle_result.state}]: {daemon_lifecycle_result.message}",
        )
        if not daemon_lifecycle_result.healthy:
            print(f"  - Guidance: {daemon_lifecycle_result.guidance}")

    if manifest_valid and manifest is not None:
        if not runtime_constraint_ok:
            if runtime_language == "nodejs":
                print("  - Action: install or upgrade Node.js so runtime.version in kinnoo.yaml is satisfied")
            else:
                print("  - Action: use a Python interpreter that satisfies runtime.version in kinnoo.yaml")
        if not env_vars_ok:
            print("  - Action: set missing env vars in your shell environment or agent-local .env file")
        if not entrypoint_ok:
            print("  - Action: ensure manifest entrypoint exists and is readable")
        if not dependencies_ok:
            if runtime_language == "nodejs":
                print("  - Action: install the configured Node package manager and ensure it is on PATH")
            else:
                print("  - Action: create agent .venv and install requirements (for example: kinnoo run <agent-dir> '<input>')")
        if service_results and not service_checks_ok:
            print("  - Action: make unhealthy services reachable or update services[].health_check settings")
        if daemon_lifecycle_result is not None and not daemon_lifecycle_result.healthy:
            print(f"  - Action: {daemon_lifecycle_result.guidance}")

    skipped_entrypoint = agent_dir_exists and manifest_exists and manifest_valid
    _emit_preflight_line(skipped_entrypoint, "entrypoint execution path skipped in preflight mode")

    if (
        agent_dir_exists
        and manifest_exists
        and manifest_valid
        and runtime_constraint_ok
        and env_vars_ok
        and entrypoint_ok
        and dependencies_ok
        and service_checks_ok
        and daemon_state_ok
    ):
        print("Ready to run")
        print("Preflight result: PASS")
        return 0

    print("Not ready to run")
    print("Remediation summary:")
    if not runtime_constraint_ok:
        if runtime_language == "nodejs":
            print("- runtime version: install or upgrade Node.js to satisfy runtime.version")
        else:
            print("- runtime version: use a compatible Python interpreter per runtime.version")
    if not env_vars_ok:
        print("- env vars: provide missing names in environment or .env")
    if not entrypoint_ok:
        print("- entrypoint: ensure manifest entrypoint exists and is readable")
    if not dependencies_ok:
        if runtime_language == "nodejs":
            print("- dependencies: install the configured Node package manager and ensure it is on PATH")
        else:
            print("- dependencies: create .venv and install requirements")
    if service_results and not service_checks_ok:
        print("- services: fix failing service checks or adjust services[].health_check configuration")
    if daemon_lifecycle_result is not None and not daemon_lifecycle_result.healthy:
        print(f"- daemon: {daemon_lifecycle_result.guidance}")

    print("Preflight result: FAIL")
    return 1


def _write_run_trace_log(
    agent_dir: Path,
    manifest: dict | None,
    exit_code: int,
    forbidden_values: Iterable[str] | None = None,
    lifecycle: dict[str, object] | None = None,
) -> None:
    now_utc = datetime.now(timezone.utc)
    timestamp_json = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    timestamp_filename = now_utc.strftime("%Y-%m-%dT%H-%M-%SZ")

    agent_name = "unknown"
    agent_version = "unknown"
    runtime_type = "unknown"
    if isinstance(manifest, dict):
        name_value = manifest.get("name")
        if isinstance(name_value, str) and name_value.strip():
            agent_name = name_value

        version_value = manifest.get("version")
        if isinstance(version_value, str) and version_value.strip():
            agent_version = version_value

        runtime_value = manifest.get("runtime")
        if isinstance(runtime_value, dict):
            runtime_type_value = runtime_value.get("type")
            if isinstance(runtime_type_value, str) and runtime_type_value.strip():
                runtime_type = runtime_type_value

    log_payload = {
        "timestamp": timestamp_json,
        "agent_name": agent_name,
        "agent-version": agent_version,
        "runtime_type": runtime_type,
        "exit_code": int(exit_code),
    }
    if runtime_type == "mcp-server" and lifecycle is not None:
        log_payload.update(lifecycle)

    logs_dir = Path.home() / ".kinnoo" / "logs"
    log_file = logs_dir / f"run.{timestamp_filename}.log"

    serialized_payload = json.dumps(log_payload)
    if forbidden_values is not None and _contains_forbidden_value(serialized_payload, forbidden_values):
        _print_safe_error(
            "Warning: Trace payload included sensitive content; redacting before log write.",
        )
        serialized_payload = _redact_secrets(serialized_payload, forbidden_values)

    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except Exception as error:
        _print_safe_error(f"Warning: Failed to create run trace log directory '{logs_dir}': {error}")
        return

    try:
        # [agent] SECURITY INVARIANT: only env var NAMES, never values
        log_file.write_text(serialized_payload, encoding="utf-8")
    except Exception as error:
        _print_safe_error(f"Warning: Failed to write run trace log '{log_file}': {error}")
        return


def stop_agent(agent_dir_arg: str) -> int:
    """Stop a tracked daemon process using persisted control-plane metadata."""
    agent_dir = Path(agent_dir_arg).resolve()
    if not agent_dir.exists() or not agent_dir.is_dir():
        _print_safe_error(f"Error: agent directory not found: {agent_dir}")
        return 1

    state_path = daemon_state_path(agent_dir)
    if not state_path.exists():
        _print_safe_error(
            f"Error: daemon state file not found: {state_path}. Start daemon with 'kinnoo run {agent_dir} <input>' first."
        )
        return 1

    try:
        state_payload = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as error:
        _print_safe_error(f"Error: failed to read daemon state metadata: {error}")
        return 1

    pid_value = state_payload.get("pid") if isinstance(state_payload, dict) else None
    if not isinstance(pid_value, int):
        _print_safe_error("Error: daemon state metadata is missing a valid integer pid")
        return 1

    stop_report = stop_daemon_pid(pid=pid_value)
    if not stop_report.terminated:
        _print_safe_error(
            "Error: daemon process did not stop after SIGTERM and SIGKILL fallback; "
            f"manual intervention required for pid {pid_value}"
        )
        return 1

    clear_daemon_state(agent_dir)

    if stop_report.already_stopped:
        print(f"[kinnoo] daemon already not running: pid={pid_value}")
        print("[kinnoo] cleared stale daemon state metadata")
        return 0

    if stop_report.sigkill_sent:
        print(f"[kinnoo] daemon stopped with fallback SIGKILL: pid={pid_value}")
    else:
        print(f"[kinnoo] daemon stopped gracefully with SIGTERM: pid={pid_value}")
    print("[kinnoo] daemon state metadata cleared")
    return 0


def attach_agent(agent_dir_arg: str) -> int:
    """Attach to a running daemon session by bridging the daemon log stream interactively."""
    agent_dir = Path(agent_dir_arg).resolve()
    if not agent_dir.exists() or not agent_dir.is_dir():
        _print_safe_error(f"Error: agent directory not found: {agent_dir}")
        return 1

    state_path = daemon_state_path(agent_dir)
    if not state_path.exists():
        _print_safe_error(
            f"Error: daemon state file not found: {state_path}. Start daemon with 'kinnoo run {agent_dir} <input>' first."
        )
        return 1

    try:
        state_payload = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as error:
        _print_safe_error(f"Error: failed to read daemon state metadata: {error}")
        return 1

    if not isinstance(state_payload, dict):
        _print_safe_error("Error: daemon state metadata is malformed")
        return 1

    runtime_type = state_payload.get("runtime_type")
    if runtime_type != "daemon":
        _print_safe_error(
            f"Error: attach is unsupported for runtime.type '{runtime_type}'. Only daemon runtime supports attach."
        )
        return 1

    runtime_language = state_payload.get("runtime_language")
    if runtime_language not in ("python", "nodejs"):
        _print_safe_error(
            f"Error: attach is unsupported for runtime.language '{runtime_language}'. Supported values: python, nodejs"
        )
        return 1

    pid_value = state_payload.get("pid")
    if not isinstance(pid_value, int):
        _print_safe_error("Error: daemon state metadata is missing a valid integer pid")
        return 1

    if not daemon_pid_is_running(pid_value):
        _print_safe_error(
            f"Error: daemon is not running for pid {pid_value}. Restart daemon before attach."
        )
        return 1

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        _print_safe_error("Error: attach requires an interactive TTY session")
        return 1

    log_path_value = state_payload.get("log_path")
    if isinstance(log_path_value, str) and log_path_value.strip():
        log_path = Path(log_path_value)
    else:
        log_path = daemon_log_path(agent_dir)

    if not log_path.exists() or not log_path.is_file():
        _print_safe_error(f"Error: daemon log file not found for attach: {log_path}")
        return 1

    print(f"[kinnoo] attach session started for pid={pid_value}")
    print(f"[kinnoo] streaming daemon log: {log_path}")
    print("[kinnoo] press Ctrl+C to detach")

    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as log_file:
            while True:
                line = log_file.readline()
                if line:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    continue

                if not daemon_pid_is_running(pid_value):
                    print("[kinnoo] daemon exited; attach session ending")
                    return 0

                time.sleep(0.1)
    except KeyboardInterrupt:
        print("[kinnoo] attach session detached by operator")
        return 0
    except Exception as error:
        _print_safe_error(f"Error: attach session failed: {error}")
        return 1


def _render_daemon_log_line(line: str, source_label: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"[{timestamp}] [{source_label}] {line.rstrip()}"


def logs_agent(agent_dir_arg: str, follow: bool = False, tail_lines: int = 20) -> int:
    """Show daemon logs with deterministic timestamp/source context and optional follow mode."""
    agent_dir = Path(agent_dir_arg).resolve()
    if not agent_dir.exists() or not agent_dir.is_dir():
        _print_safe_error(f"Error: agent directory not found: {agent_dir}")
        return 1

    if tail_lines < 1:
        _print_safe_error("Error: --tail must be a positive integer")
        return 1

    state_path = daemon_state_path(agent_dir)
    if not state_path.exists():
        _print_safe_error(
            f"Error: daemon state file not found: {state_path}. Start daemon with 'kinnoo run {agent_dir} <input>' first."
        )
        return 1

    try:
        state_payload = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as error:
        _print_safe_error(f"Error: failed to read daemon state metadata: {error}")
        return 1

    if not isinstance(state_payload, dict):
        _print_safe_error("Error: daemon state metadata is malformed")
        return 1

    runtime_type = state_payload.get("runtime_type")
    if runtime_type != "daemon":
        _print_safe_error(
            f"Error: logs is unsupported for runtime.type '{runtime_type}'. Only daemon runtime supports logs."
        )
        return 1

    pid_value = state_payload.get("pid")
    if not isinstance(pid_value, int):
        _print_safe_error("Error: daemon state metadata is missing a valid integer pid")
        return 1

    log_path_value = state_payload.get("log_path")
    if isinstance(log_path_value, str) and log_path_value.strip():
        log_path = Path(log_path_value)
    else:
        log_path = daemon_log_path(agent_dir)

    if not log_path.exists() or not log_path.is_file():
        _print_safe_error(
            f"Error: daemon log file not found: {log_path}. Restart daemon to recreate log output."
        )
        return 1

    try:
        all_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as error:
        _print_safe_error(f"Error: failed to read daemon log file '{log_path}': {error}")
        return 1

    daemon_running = daemon_pid_is_running(pid_value)
    if follow and not daemon_running:
        _print_safe_error(
            f"Error: daemon is not running for pid {pid_value}; follow mode requires an active daemon."
        )
        return 1

    source_label = log_path.name
    print(f"[kinnoo] daemon logs source: {log_path}")
    print(f"[kinnoo] mode: {'follow' if follow else 'tail'} (tail={tail_lines})")
    if not daemon_running:
        print(f"[kinnoo] daemon not running for pid {pid_value}; showing last available log lines")

    recent_lines = all_lines[-tail_lines:]
    for line in recent_lines:
        print(_render_daemon_log_line(line, source_label))

    if not follow:
        return 0

    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as log_file:
            log_file.seek(0, os.SEEK_END)
            while True:
                line = log_file.readline()
                if line:
                    print(_render_daemon_log_line(line, source_label))
                    continue

                if not daemon_pid_is_running(pid_value):
                    print("[kinnoo] daemon exited; follow mode ended")
                    return 0

                time.sleep(0.1)
    except KeyboardInterrupt:
        print("[kinnoo] log follow interrupted by operator")
        return 0
    except Exception as error:
        _print_safe_error(f"Error: daemon log follow failed: {error}")
        return 1


def run_agent(
    agent_dir_arg: str,
    input_arg: str | None,
    json_input_arg: str | None = None,
    json_file_arg: str | None = None,
    preflight: bool = False,
    no_guard: bool = False,
    pass_through_args: list[str] | None = None,
    sandbox: bool = False,
) -> int:
    runtime_pass_through_args = list(pass_through_args or [])
    if preflight:
        return run_preflight(agent_dir_arg)

    agent_dir = Path(agent_dir_arg).resolve()
    trace_manifest: dict | None = None
    trace_lifecycle: dict[str, object] | None = None
    trace_forbidden_values: list[str] = []
    runtime_monitor: RuntimeMonitor | None = None
    if input_arg is not None:
        trace_forbidden_values.append(input_arg)
    trace_forbidden_values.extend(runtime_pass_through_args)

    def finalize(exit_code: int) -> int:
        if runtime_monitor is not None:
            runtime_monitor.finalize(exit_code=exit_code)
        _write_run_trace_log(
            agent_dir=agent_dir,
            manifest=trace_manifest,
            exit_code=exit_code,
            forbidden_values=trace_forbidden_values,
            lifecycle=trace_lifecycle,
        )
        return exit_code

    if not os.access(agent_dir, os.R_OK | os.X_OK):
        _print_safe_error(f"Error: Permission denied while accessing agent directory: {agent_dir}")
        return finalize(1)

    kinnoo_yaml = agent_dir / "kinnoo.yaml"

    if not kinnoo_yaml.exists():
        _print_safe_error(f"Error: kinnoo.yaml not found in {agent_dir}")
        return finalize(1)

    try:
        with open(kinnoo_yaml, "r") as manifest_file:
            try:
                manifest = yaml.safe_load(manifest_file)
            except yaml.YAMLError as error:
                _print_safe_error(f"Error: kinnoo.yaml is corrupted or invalid YAML: {error}")
                return finalize(1)
    except PermissionError as error:
        _print_safe_error(f"Error: Permission denied while reading kinnoo.yaml: {error}")
        return finalize(1)
    except Exception as error:
        _print_safe_error(f"Error parsing kinnoo.yaml: {error}")
        return finalize(1)

    if isinstance(manifest, dict):
        trace_manifest = manifest

    runtime_section = manifest.get("runtime") if isinstance(manifest.get("runtime"), dict) else {}
    runtime_language_raw = runtime_section.get("language") if isinstance(runtime_section.get("language"), str) else "python"
    runtime_language = runtime_language_raw.strip().lower() or "python"

    try:
        effective_input_arg = _resolve_effective_input_arg(
            manifest=manifest if isinstance(manifest, dict) else {},
            input_arg=input_arg,
            json_input_arg=json_input_arg,
            json_file_arg=json_file_arg,
            secret_values=trace_forbidden_values,
        )
    except ValueError as error:
        _print_safe_error(str(error), secret_values=trace_forbidden_values)
        return finalize(1)

    python_exe: Path | None = None
    if runtime_language == "python":
        venv_dir = agent_dir / ".venv"
        requirements = agent_dir / "requirements.txt"

        if not venv_dir.exists():
            try:
                venv.create(venv_dir, with_pip=True)
            except PermissionError as error:
                _print_safe_error(f"Error: Permission denied while creating .venv in {agent_dir}: {error}")
                return finalize(1)
            except Exception as error:
                _print_safe_error(f"Error: Failed to create .venv in {agent_dir}: {error}")
                return finalize(1)

        if requirements.exists() and requirements.read_text().strip():
            pip_exe = venv_dir / "bin" / "pip"
            if not pip_exe.exists():
                pip_exe = venv_dir / "Scripts" / "pip.exe"
            if not pip_exe.exists():
                _print_safe_error(f"Error: pip not found in venv at {pip_exe}")
                return finalize(1)
            print("[kinnoo] installing requirements for running agent...")
            try:
                install_result = subprocess.run(
                    [str(pip_exe), "install", "-r", str(requirements)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except PermissionError as error:
                _print_safe_error(f"Error: Permission denied while installing requirements in {agent_dir}: {error}")
                return finalize(1)
            except Exception as error:
                _print_safe_error(f"Error: Failed to install requirements in {agent_dir}: {error}")
                return finalize(1)

            if install_result.returncode != 0:
                _print_safe_error(
                    "Error: Failed to install requirements for running agent. Please check your requirements.txt and try again.",
                )
                return finalize(install_result.returncode)

        python_exe = venv_dir / "bin" / "python"
        if not python_exe.exists():
            python_exe = venv_dir / "Scripts" / "python.exe"
        if not python_exe.exists():
            _print_safe_error(f"Error: python not found in venv at {python_exe}")
            return finalize(1)
    elif runtime_language != "nodejs":
        _print_safe_error(
            f"Error: Unsupported runtime.language '{runtime_language}'. Supported values are: python, nodejs"
        )
        return finalize(1)

    inputs_required = _manifest_inputs_required(manifest)
    if effective_input_arg is None and inputs_required:
        _print_safe_error("Error: input is required for kinnoo run unless --preflight is used")
        return finalize(1)

    entrypoint = manifest.get("entrypoint")
    if not entrypoint:
        _print_safe_error("Error: 'entrypoint' not specified in kinnoo.yaml")
        return finalize(1)

    declared_env_vars = normalize_env_vars(manifest.get("env_vars"))
    dotenv_values = _load_agent_dotenv(agent_dir / ".env")
    resolved_env_vars: dict[str, str] = {}
    missing_env_vars: list[str] = []
    for env_var_name in declared_env_vars:
        env_var_value = os.environ.get(env_var_name)
        if env_var_value is not None:
            resolved_env_vars[env_var_name] = env_var_value
            continue

        dotenv_value = dotenv_values.get(env_var_name)
        if dotenv_value is not None:
            resolved_env_vars[env_var_name] = dotenv_value
            continue

        missing_env_vars.append(env_var_name)

    if missing_env_vars:
        for env_var_name in missing_env_vars:
            try:
                prompted_value = getpass.getpass(
                    f"Enter value for {env_var_name}: "
                )
            except (KeyboardInterrupt, EOFError):
                _print_safe_error(
                    f"Error: Missing required environment variable: {env_var_name}",
                )
                return finalize(1)

            if not prompted_value:
                _print_safe_error(
                    f"Error: Missing required environment variable: {env_var_name}",
                )
                return finalize(1)

            resolved_env_vars[env_var_name] = prompted_value

    trace_forbidden_values.extend(resolved_env_vars.values())

    service_results = _run_service_checks(manifest if isinstance(manifest, dict) else None)
    if service_results:
        print("[kinnoo] Service health checks:", flush=True)
        for service_result in service_results:
            _render_service_check_for_run(service_result)

    unhealthy_service_results = [
        service_result for service_result in service_results if not service_result.healthy
    ]
    if unhealthy_service_results:
        if not sys.stdin.isatty():
            print(
                "Non-interactive mode: aborting due to unhealthy service check.",
                file=sys.stderr,
            )
            return finalize(1)

        # Prompt once per unhealthy service so users can decide to proceed with explicit context.
        for service_result in unhealthy_service_results:
            try:
                response = input(
                    f"Service {service_result.service_name} is not healthy. Proceed anyway? [y/N] "
                ).strip().lower()
            except (KeyboardInterrupt, EOFError):
                return finalize(1)
            if response != "y":
                return finalize(1)

    runtime_type = runtime_section.get("type") if isinstance(runtime_section.get("type"), str) else "one-shot"

    if sandbox:
        sandbox_decision = evaluate_sandbox_permissions(
            manifest=manifest if isinstance(manifest, dict) else {},
            runtime_type=runtime_type,
            runtime_language=runtime_language,
            pass_through_args=runtime_pass_through_args,
        )
        if not sandbox_decision.allowed:
            enforcement_mode = os.environ.get("KINNOO_MONITOR_ENFORCEMENT_MODE", "terminate")
            enforcement_decision = resolve_violation_enforcement(
                capability=sandbox_decision.capability or "unspecified",
                configured_mode=enforcement_mode,
            )
            violation_event = {
                "event_type": "permission_violation",
                "boundary": "run",
                "classification": sandbox_decision.code,
                "runtime_language": runtime_language,
                "runtime_type": runtime_type,
                "capability": sandbox_decision.capability or "unspecified",
                "attempted_action": sandbox_decision.action or "unspecified",
                "message": sandbox_decision.message,
                "remediation": sandbox_decision.remediation,
                "enforcement_action": enforcement_decision.action,
                "reason_code": enforcement_decision.reason_code,
            }
            emit_violation_event_diagnostic(
                violation_event,
                secret_values=trace_forbidden_values,
            )
            violation_trace_path = write_violation_event(
                target_dir=agent_dir,
                payload=violation_event,
            )
            if violation_trace_path is not None:
                print(f"[kinnoo] violation event logged: '{violation_trace_path}'", file=sys.stderr)

            if enforcement_decision.action == "warn_continue":
                _print_safe_error(
                    "Warning: runtime policy violation allowed in warn mode "
                    f"(reason_code={enforcement_decision.reason_code}); execution continues.",
                    secret_values=resolved_env_vars.values(),
                )
                print("[kinnoo] sandbox policy warning recorded", flush=True)
            else:
                _print_safe_error(
                    "Error: kill switch activated for runtime policy violation "
                    f"(reason_code={enforcement_decision.reason_code}).",
                    secret_values=resolved_env_vars.values(),
                )
                _print_safe_error(
                    "Error: sandbox enforcement failed "
                    f"(classification={sandbox_decision.code}): {sandbox_decision.message}",
                    secret_values=resolved_env_vars.values(),
                )
                _print_safe_error(
                    f"Remediation: {sandbox_decision.remediation}",
                    secret_values=resolved_env_vars.values(),
                )
                return finalize(1)

        print("[kinnoo] sandbox policy check passed", flush=True)

    # Evaluate the user input before entrypoint execution; this is warning-based and never hard-rejects
    # when a user explicitly confirms in interactive mode.
    if not no_guard:
        from .input_guard import get_default_guard

        guard = get_default_guard()
        aggregate_warnings = []

        if effective_input_arg is not None:
            guard_result = guard.check(effective_input_arg, "text")
            aggregate_warnings.extend(guard_result.warnings)

        pass_through_inputs = _build_pass_through_guard_inputs(runtime_pass_through_args)
        if pass_through_inputs:
            guard_result = guard.check_inputs(pass_through_inputs)
            aggregate_warnings.extend(guard_result.warnings)

        if aggregate_warnings:
            print("[kinnoo] Input safety warning:", file=sys.stderr)
            for warning in aggregate_warnings:
                param_suffix = f" (param: {warning.param_name})" if warning.param_name else ""
                print(
                    f"  - [{warning.threat_category}] {warning.description}{param_suffix}",
                    file=sys.stderr,
                )
            if sys.stdin.isatty():
                try:
                    response = input("Proceed anyway? [y/N]: ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    return finalize(1)
                if response != "y":
                    return finalize(1)
            else:
                print(
                    "Non-interactive mode: aborting due to input safety warning.",
                    file=sys.stderr,
                )
                return finalize(1)

    entrypoint_path = agent_dir / entrypoint
    if not entrypoint_path.exists():
        _print_safe_error(f"Error: Entrypoint file '{entrypoint}' not found in {agent_dir}")
        return finalize(1)

    subprocess_env = os.environ.copy()
    subprocess_env.update(resolved_env_vars)

    if runtime_language == "nodejs":
        process_args = ["node", str(entrypoint_path)]
    else:
        process_args = [str(python_exe), str(entrypoint_path)]
    if effective_input_arg is not None:
        process_args.append(effective_input_arg)
    process_args.extend(runtime_pass_through_args)

    runtime_monitor = RuntimeMonitor(
        agent_dir=agent_dir,
        runtime_language=runtime_language,
        forbidden_values=trace_forbidden_values,
    )
    subprocess_env = runtime_monitor.prepare_environment(
        process_args=process_args,
        cwd=agent_dir,
        env=subprocess_env,
    )

    enforce_json_output_contract = (
        runtime_type not in ("mcp-server", "daemon")
        and _manifest_declares_json_output(manifest if isinstance(manifest, dict) else {})
    )

    if runtime_type == "daemon":
        # Daemon mode must detach from the caller terminal and persist control-plane state.
        try:
            log_path = daemon_log_path(agent_dir)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as daemon_log:
                process = subprocess.Popen(
                    process_args,
                    cwd=agent_dir,
                    stdout=daemon_log,
                    stderr=subprocess.STDOUT,
                    env=subprocess_env,
                    start_new_session=True,
                )

            state_payload = build_daemon_state_payload(
                agent_dir=agent_dir,
                runtime_language=runtime_language,
                runtime_type=runtime_type,
                entrypoint=str(entrypoint),
                process_id=process.pid,
                process_args=process_args,
                log_path=log_path,
            )
            state_path = write_daemon_state(agent_dir, state_payload)
        except Exception as error:
            _print_safe_error(
                f"Error: Failed to launch daemon process: {error}",
                secret_values=resolved_env_vars.values(),
            )
            return finalize(1)

        print(f"[kinnoo] daemon started: pid={process.pid}")
        print(f"[kinnoo] daemon state file: {state_path}")
        print(f"[kinnoo] daemon log file: {log_path}")
        print("[kinnoo] control hints: use 'kinnoo stop <agent-dir>' to terminate")
        return finalize(0)

    if runtime_type == "mcp-server":
        shutdown_timeout_value = runtime_section.get("shutdown_timeout_seconds", 3.0)
        if isinstance(shutdown_timeout_value, (int, float)) and shutdown_timeout_value > 0:
            shutdown_timeout_seconds = float(shutdown_timeout_value)
        else:
            shutdown_timeout_seconds = 3.0

        def _stdout_callback(line: str) -> None:
            sys.stdout.write(line)
            sys.stdout.flush()

        def _stderr_callback(line: str) -> None:
            sys.stderr.write(line)
            sys.stderr.flush()

        try:
            process = start_server(
                process_args,
                cwd=agent_dir,
                env=subprocess_env,
            )
        except Exception as error:
            _print_safe_error(
                f"Error: Failed to launch mcp-server process: {error}",
                secret_values=resolved_env_vars.values(),
            )
            return finalize(1)

        interrupted = False
        previous_sigint_handler = signal.getsignal(signal.SIGINT)

        def _sigint_handler(_signum, _frame):
            nonlocal interrupted
            interrupted = True

        signal.signal(signal.SIGINT, _sigint_handler)

        try:
            stream_state = stream_output(
                process,
                stdout_callback=_stdout_callback,
                stderr_callback=_stderr_callback,
            )
            readiness = infer_readiness_config(runtime_section)
            is_ready = wait_until_ready(process, readiness, stream_state)
            if not is_ready:
                _print_safe_error("Error: mcp-server failed readiness probe and did not become ready")
                shutdown_server(process)
                return finalize(1)

            server_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            shutdown_sigterm_sent = False
            shutdown_sigkill_sent = False
            return_code: int

            while True:
                if interrupted:
                    shutdown_report = shutdown_server_with_report(
                        process,
                        timeout_seconds=shutdown_timeout_seconds,
                    )
                    return_code = shutdown_report.exit_code
                    shutdown_sigterm_sent = shutdown_report.sigterm_sent
                    shutdown_sigkill_sent = shutdown_report.sigkill_sent
                    break

                polled_code = process.poll()
                if polled_code is not None:
                    return_code = int(polled_code)
                    break
                time.sleep(0.05)

            server_stop = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            server_signal = None
            if return_code < 0:
                try:
                    server_signal = signal.Signals(-return_code).name
                except Exception:
                    server_signal = f"SIG{-return_code}"
            trace_lifecycle = {
                "start_timestamp": server_start,
                "stop_timestamp": server_stop,
                "server_exit_code": int(return_code),
                "server_exit_signal": server_signal,
                "shutdown_sigterm_sent": shutdown_sigterm_sent,
                "shutdown_sigkill_sent": shutdown_sigkill_sent,
            }

            if stream_state.stdout_thread is not None:
                stream_state.stdout_thread.join(timeout=0.2)
            if stream_state.stderr_thread is not None:
                stream_state.stderr_thread.join(timeout=0.2)

            return finalize(return_code)
        finally:
            signal.signal(signal.SIGINT, previous_sigint_handler)

    try:
        if enforce_json_output_contract:
            process = subprocess.Popen(
                process_args,
                cwd=agent_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=subprocess_env,
                text=True,
                bufsize=1,
            )
            captured_stdout, _captured_stderr = _stream_and_capture_process_output(process)
            if process.returncode != 0:
                return finalize(process.returncode)

            try:
                json.loads(captured_stdout)
            except json.JSONDecodeError as error:
                _print_safe_error(
                    "Error: outputs.type=json contract violation: stdout is not valid JSON "
                    f"(line {error.lineno}, column {error.colno}: {error.msg})",
                    secret_values=resolved_env_vars.values(),
                )
                return finalize(1)

            return finalize(process.returncode)

        process = subprocess.Popen(
            process_args,
            cwd=agent_dir,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=subprocess_env,
        )
        process.communicate()
        return finalize(process.returncode)
    except Exception as error:
        _print_safe_error(
            f"Error: Failed to launch agent entrypoint process: {error}",
            secret_values=resolved_env_vars.values(),
        )
        return finalize(1)
