from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path
import os
import getpass
from typing import Iterable

import yaml

from .schema import normalize_env_vars
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
    if manifest_exists:
        manifest_valid, manifest_errors = validate(str(kinnoo_yaml))
        _emit_preflight_line(manifest_valid, "manifest validates against kinnoo schema")
        if not manifest_valid:
            for manifest_error in manifest_errors:
                print(f"  - {manifest_error}")

    skipped_entrypoint = agent_dir_exists and manifest_exists and manifest_valid
    _emit_preflight_line(skipped_entrypoint, "entrypoint execution path skipped in preflight mode")

    if agent_dir_exists and manifest_exists and manifest_valid:
        print("Preflight result: PASS")
        return 0

    print("Preflight result: FAIL")
    return 1


def run_agent(agent_dir_arg: str, input_arg: str | None, preflight: bool = False) -> int:
    if preflight:
        return run_preflight(agent_dir_arg)

    if input_arg is None:
        _print_safe_error("Error: input is required for kinnoo run unless --preflight is used")
        return 1

    agent_dir = Path(agent_dir_arg).resolve()
    venv_dir = agent_dir / ".venv"
    requirements = agent_dir / "requirements.txt"
    kinnoo_yaml = agent_dir / "kinnoo.yaml"

    if not venv_dir.exists():
        try:
            venv.create(venv_dir, with_pip=True)
        except PermissionError as error:
            _print_safe_error(f"Error: Permission denied while creating .venv in {agent_dir}: {error}")
            return 1
        except Exception as error:
            _print_safe_error(f"Error: Failed to create .venv in {agent_dir}: {error}")
            return 1

    if requirements.exists() and requirements.read_text().strip():
        pip_exe = venv_dir / "bin" / "pip"
        if not pip_exe.exists():
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        if not pip_exe.exists():
            _print_safe_error(f"Error: pip not found in venv at {pip_exe}")
            return 1
        print("[kinnoo] installing requirements for running agent...")
        try:
            install_result = subprocess.run(
                [str(pip_exe), "install", "-r", str(requirements)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except PermissionError as error:
            _print_safe_error(f"Error: Permission denied while installing requirements in {agent_dir}: {error}")
            return 1
        except Exception as error:
            _print_safe_error(f"Error: Failed to install requirements in {agent_dir}: {error}")
            return 1

        if install_result.returncode != 0:
            _print_safe_error(
                "Error: Failed to install requirements for running agent. Please check your requirements.txt and try again.",
            )
            return install_result.returncode

    if not kinnoo_yaml.exists():
        _print_safe_error(f"Error: kinnoo.yaml not found in {agent_dir}")
        return 1

    try:
        with open(kinnoo_yaml, "r") as manifest_file:
            try:
                manifest = yaml.safe_load(manifest_file)
            except yaml.YAMLError as error:
                _print_safe_error(f"Error: kinnoo.yaml is corrupted or invalid YAML: {error}")
                return 1
    except PermissionError as error:
        _print_safe_error(f"Error: Permission denied while reading kinnoo.yaml: {error}")
        return 1
    except Exception as error:
        _print_safe_error(f"Error parsing kinnoo.yaml: {error}")
        return 1

    entrypoint = manifest.get("entrypoint")
    if not entrypoint:
        _print_safe_error("Error: 'entrypoint' not specified in kinnoo.yaml")
        return 1

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
                return 1

            if not prompted_value:
                _print_safe_error(
                    f"Error: Missing required environment variable: {env_var_name}",
                )
                return 1

            resolved_env_vars[env_var_name] = prompted_value

    entrypoint_path = agent_dir / entrypoint
    if not entrypoint_path.exists():
        _print_safe_error(f"Error: Entrypoint file '{entrypoint}' not found in {agent_dir}")
        return 1

    python_exe = venv_dir / "bin" / "python"
    if not python_exe.exists():
        python_exe = venv_dir / "Scripts" / "python.exe"
    if not python_exe.exists():
        _print_safe_error(f"Error: python not found in venv at {python_exe}")
        return 1

    subprocess_env = os.environ.copy()
    subprocess_env.update(resolved_env_vars)

    try:
        process = subprocess.Popen(
            [str(python_exe), str(entrypoint_path), input_arg],
            cwd=agent_dir,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=subprocess_env,
        )
        process.communicate()
        return process.returncode
    except Exception as error:
        _print_safe_error(
            f"Error: Failed to launch agent entrypoint process: {error}",
            secret_values=resolved_env_vars.values(),
        )
        return 1
