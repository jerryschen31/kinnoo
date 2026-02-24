"""
CLI entry point for kinnoo.
Handles argument parsing and dispatches subcommands.
"""
import argparse
import sys
import re
from pathlib import Path

try:
    from kinnoo.schema import NAME_PATTERN
except ImportError:
    # fallback for direct script execution
    from .schema import NAME_PATTERN

def main():
    parser = argparse.ArgumentParser(prog="kinnoo", description="Kinnoo CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init subcommand
    init_parser = subparsers.add_parser("init", help="Scaffold a new kinnoo agent")
    init_parser.add_argument("agent_name", nargs="?", help="Name of the agent to create")
    init_parser.add_argument(
        "--framework",
        choices=["gemini", "chatgpt", "claude-chat"],
        help="(Optional) Pre-populate agent with LLM framework template (gemini, chatgpt, claude-chat)"
    )

    # Add 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run a kinnoo agent")
    run_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory")
    run_parser.add_argument("input", nargs="?", help="Input string to pass to the agent entrypoint")

    # Pre-parse sys.argv for missing args to print custom usage before argparse error
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        if len(sys.argv) < 4:
            print("Usage: kinnoo run <agent-dir> '<input>'", file=sys.stderr)
            sys.exit(1)

    args = parser.parse_args()

    if args.command == "init":
        if not args.agent_name:
            print("Usage: kinnoo init <agent-name>", file=sys.stderr)
            sys.exit(1)
        if not re.match(NAME_PATTERN, args.agent_name):
            print(f"Error: Invalid agent name '{args.agent_name}'. Must match pattern: {NAME_PATTERN}", file=sys.stderr)
            sys.exit(1)
        from kinnoo.init_command import init_agent
        # from pathlib import Path
        try:
            init_agent(args.agent_name, Path.cwd(), framework=args.framework)
            print(f"Initialized agent: {args.agent_name}")
        except FileExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "run":
        if not hasattr(args, "agent_dir") or args.agent_dir is None or args.input is None:
            print("Usage: kinnoo run <agent-dir> '<input>'", file=sys.stderr)
            sys.exit(1)
        agent_dir = Path(args.agent_dir).resolve()
        venv_dir = agent_dir / ".venv"
        requirements = agent_dir / "requirements.txt"
        kinnoo_yaml = agent_dir / "kinnoo.yaml"
        import subprocess
        import yaml

        # Ensure .venv exists (task8, assumed done)
        if not venv_dir.exists():
            import venv
            try:
                venv.create(venv_dir, with_pip=True)
            except PermissionError as e:
                print(f"Error: Permission denied while creating .venv in {agent_dir}: {e}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error: Failed to create .venv in {agent_dir}: {e}", file=sys.stderr)
                sys.exit(1)

        # Install requirements.txt packages into venv
        if requirements.exists() and requirements.read_text().strip():
            pip_exe = venv_dir / "bin" / "pip"
            if not pip_exe.exists():
                pip_exe = venv_dir / "Scripts" / "pip.exe"  # Windows fallback
            if not pip_exe.exists():
                print(f"Error: pip not found in venv at {pip_exe}", file=sys.stderr)
                sys.exit(1)
            print("[kinnoo] installing requirements for running agent...")
            try:
                # Suppress pip output by redirecting stdout and stderr to DEVNULL
                result = subprocess.run(
                    [str(pip_exe), "install", "-r", str(requirements)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except PermissionError as e:
                print(f"Error: Permission denied while installing requirements in {agent_dir}: {e}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error: Failed to install requirements in {agent_dir}: {e}", file=sys.stderr)
                sys.exit(1)
            if result.returncode != 0:
                print("Error: Failed to install requirements for running agent. Please check your requirements.txt and try again.", file=sys.stderr)
                sys.exit(result.returncode)

        # Validate kinnoo.yaml manifest (task7, assumed done)
        if not kinnoo_yaml.exists():
            print(f"Error: kinnoo.yaml not found in {agent_dir}", file=sys.stderr)
            sys.exit(1)

        # Parse kinnoo.yaml to get entrypoint
        try:
            with open(kinnoo_yaml, "r") as f:
                try:
                    manifest = yaml.safe_load(f)
                except yaml.YAMLError as ye:
                    print(f"Error: kinnoo.yaml is corrupted or invalid YAML: {ye}", file=sys.stderr)
                    sys.exit(1)
        except PermissionError as e:
            print(f"Error: Permission denied while reading kinnoo.yaml: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing kinnoo.yaml: {e}", file=sys.stderr)
            sys.exit(1)

        entrypoint = manifest.get("entrypoint")
        if not entrypoint:
            print("Error: 'entrypoint' not specified in kinnoo.yaml", file=sys.stderr)
            sys.exit(1)

        entrypoint_path = agent_dir / entrypoint
        if not entrypoint_path.exists():
            print(f"Error: Entrypoint file '{entrypoint}' not found in {agent_dir}", file=sys.stderr)
            sys.exit(1)

        # Find python executable in venv
        python_exe = venv_dir / "bin" / "python"
        if not python_exe.exists():
            python_exe = venv_dir / "Scripts" / "python.exe"  # Windows fallback
        if not python_exe.exists():
            print(f"Error: python not found in venv at {python_exe}", file=sys.stderr)
            sys.exit(1)

        # Prepare input argument
        input_arg = args.input if args.input is not None else ""

        # Run entrypoint with input as sys.argv[1], streaming stdout and stderr
        process = subprocess.Popen(
            [str(python_exe), str(entrypoint_path), input_arg],
            cwd=agent_dir,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        process.communicate()
        sys.exit(process.returncode)

if __name__ == "__main__":
    main()
