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
from datetime import datetime, timezone

import yaml

from .schema import normalize_env_vars
from .supervisor import (
    infer_readiness_config,
    shutdown_server_with_report,
    shutdown_server,
    start_server,
    stream_output,
    wait_until_ready,
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

    runtime_constraint_ok = False
    runtime_message = "runtime version check failed: manifest validation prerequisite not met"
    env_vars_ok = False
    env_vars_message = "env vars check failed: manifest validation prerequisite not met"
    entrypoint_ok = False
    entrypoint_message = "entrypoint check failed: manifest validation prerequisite not met"
    dependencies_ok = False
    dependencies_message = "dependency readiness check failed: manifest validation prerequisite not met"
    if manifest_valid and manifest is not None:
        runtime_version_constraint = str(
            manifest.get("runtime", {}).get("version", "")
            if isinstance(manifest.get("runtime", {}), dict)
            else ""
        )
        runtime_constraint_ok, runtime_message = _check_runtime_version_constraint(runtime_version_constraint)

        env_vars_ok, env_vars_message = _check_preflight_env_vars(manifest, agent_dir)

        entrypoint_ok, entrypoint_message = _check_preflight_entrypoint(manifest, agent_dir)

        dependencies_ok, dependencies_message = _check_preflight_dependencies(manifest, agent_dir)

    _emit_preflight_line(runtime_constraint_ok, runtime_message)
    _emit_preflight_line(env_vars_ok, env_vars_message)
    _emit_preflight_line(entrypoint_ok, entrypoint_message)
    _emit_preflight_line(dependencies_ok, dependencies_message)

    if manifest_valid and manifest is not None:
        if not runtime_constraint_ok:
            print("  - Action: use a Python interpreter that satisfies runtime.version in kinnoo.yaml")
        if not env_vars_ok:
            print("  - Action: set missing env vars in your shell environment or agent-local .env file")
        if not entrypoint_ok:
            print("  - Action: ensure manifest entrypoint exists and is readable")
        if not dependencies_ok:
            print("  - Action: create agent .venv and install requirements (for example: kinnoo run <agent-dir> '<input>')")

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
    ):
        print("Ready to run")
        print("Preflight result: PASS")
        return 0

    print("Not ready to run")
    print("Remediation summary:")
    if not runtime_constraint_ok:
        print("- runtime version: use a compatible Python interpreter per runtime.version")
    if not env_vars_ok:
        print("- env vars: provide missing names in environment or .env")
    if not entrypoint_ok:
        print("- entrypoint: ensure manifest entrypoint exists and is readable")
    if not dependencies_ok:
        print("- dependencies: create .venv and install requirements")

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


def run_agent(
    agent_dir_arg: str,
    input_arg: str | None,
    preflight: bool = False,
    no_guard: bool = False,
    pass_through_args: list[str] | None = None,
) -> int:
    runtime_pass_through_args = list(pass_through_args or [])
    if preflight:
        return run_preflight(agent_dir_arg)

    agent_dir = Path(agent_dir_arg).resolve()
    trace_manifest: dict | None = None
    trace_lifecycle: dict[str, object] | None = None
    trace_forbidden_values: list[str] = []
    if input_arg is not None:
        trace_forbidden_values.append(input_arg)
    trace_forbidden_values.extend(runtime_pass_through_args)

    def finalize(exit_code: int) -> int:
        _write_run_trace_log(
            agent_dir=agent_dir,
            manifest=trace_manifest,
            exit_code=exit_code,
            forbidden_values=trace_forbidden_values,
            lifecycle=trace_lifecycle,
        )
        return exit_code

    venv_dir = agent_dir / ".venv"
    requirements = agent_dir / "requirements.txt"
    kinnoo_yaml = agent_dir / "kinnoo.yaml"

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

    inputs_required = _manifest_inputs_required(manifest)
    if input_arg is None and inputs_required:
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

    # Evaluate the user input before entrypoint execution; this is warning-based and never hard-rejects
    # when a user explicitly confirms in interactive mode.
    if not no_guard:
        from .input_guard import get_default_guard

        guard = get_default_guard()
        aggregate_warnings = []

        if input_arg is not None:
            guard_result = guard.check(input_arg, "text")
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

    python_exe = venv_dir / "bin" / "python"
    if not python_exe.exists():
        python_exe = venv_dir / "Scripts" / "python.exe"
    if not python_exe.exists():
        _print_safe_error(f"Error: python not found in venv at {python_exe}")
        return finalize(1)

    subprocess_env = os.environ.copy()
    subprocess_env.update(resolved_env_vars)

    process_args = [str(python_exe), str(entrypoint_path)]
    if input_arg is not None:
        process_args.append(input_arg)
    process_args.extend(runtime_pass_through_args)

    runtime_section = manifest.get("runtime") if isinstance(manifest.get("runtime"), dict) else {}
    runtime_type = runtime_section.get("type") if isinstance(runtime_section.get("type"), str) else "one-shot"

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
