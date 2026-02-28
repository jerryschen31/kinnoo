from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path
import os

import yaml

from .schema import normalize_env_vars


def run_agent(agent_dir_arg: str, input_arg: str) -> int:
    agent_dir = Path(agent_dir_arg).resolve()
    venv_dir = agent_dir / ".venv"
    requirements = agent_dir / "requirements.txt"
    kinnoo_yaml = agent_dir / "kinnoo.yaml"

    if not venv_dir.exists():
        try:
            venv.create(venv_dir, with_pip=True)
        except PermissionError as error:
            print(f"Error: Permission denied while creating .venv in {agent_dir}: {error}", file=sys.stderr)
            return 1
        except Exception as error:
            print(f"Error: Failed to create .venv in {agent_dir}: {error}", file=sys.stderr)
            return 1

    if requirements.exists() and requirements.read_text().strip():
        pip_exe = venv_dir / "bin" / "pip"
        if not pip_exe.exists():
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        if not pip_exe.exists():
            print(f"Error: pip not found in venv at {pip_exe}", file=sys.stderr)
            return 1
        print("[kinnoo] installing requirements for running agent...")
        try:
            install_result = subprocess.run(
                [str(pip_exe), "install", "-r", str(requirements)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except PermissionError as error:
            print(f"Error: Permission denied while installing requirements in {agent_dir}: {error}", file=sys.stderr)
            return 1
        except Exception as error:
            print(f"Error: Failed to install requirements in {agent_dir}: {error}", file=sys.stderr)
            return 1

        if install_result.returncode != 0:
            print(
                "Error: Failed to install requirements for running agent. Please check your requirements.txt and try again.",
                file=sys.stderr,
            )
            return install_result.returncode

    if not kinnoo_yaml.exists():
        print(f"Error: kinnoo.yaml not found in {agent_dir}", file=sys.stderr)
        return 1

    try:
        with open(kinnoo_yaml, "r") as manifest_file:
            try:
                manifest = yaml.safe_load(manifest_file)
            except yaml.YAMLError as error:
                print(f"Error: kinnoo.yaml is corrupted or invalid YAML: {error}", file=sys.stderr)
                return 1
    except PermissionError as error:
        print(f"Error: Permission denied while reading kinnoo.yaml: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Error parsing kinnoo.yaml: {error}", file=sys.stderr)
        return 1

    entrypoint = manifest.get("entrypoint")
    if not entrypoint:
        print("Error: 'entrypoint' not specified in kinnoo.yaml", file=sys.stderr)
        return 1

    declared_env_vars = normalize_env_vars(manifest.get("env_vars"))
    resolved_env_vars: dict[str, str] = {}
    missing_env_vars: list[str] = []
    for env_var_name in declared_env_vars:
        env_var_value = os.environ.get(env_var_name)
        if env_var_value is None:
            missing_env_vars.append(env_var_name)
            continue
        resolved_env_vars[env_var_name] = env_var_value

    if missing_env_vars:
        missing_names = ", ".join(missing_env_vars)
        print(
            f"Error: Missing required environment variables: {missing_names}",
            file=sys.stderr,
        )
        return 1

    entrypoint_path = agent_dir / entrypoint
    if not entrypoint_path.exists():
        print(f"Error: Entrypoint file '{entrypoint}' not found in {agent_dir}", file=sys.stderr)
        return 1

    python_exe = venv_dir / "bin" / "python"
    if not python_exe.exists():
        python_exe = venv_dir / "Scripts" / "python.exe"
    if not python_exe.exists():
        print(f"Error: python not found in venv at {python_exe}", file=sys.stderr)
        return 1

    subprocess_env = os.environ.copy()
    subprocess_env.update(resolved_env_vars)

    process = subprocess.Popen(
        [str(python_exe), str(entrypoint_path), input_arg],
        cwd=agent_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=subprocess_env,
    )
    process.communicate()
    return process.returncode
