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

    # Add 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run a kinnoo agent")
    run_parser.add_argument("agent_dir", help="Path to agent directory")

    args = parser.parse_args()

    if args.command == "init":
        if not args.agent_name:
            print("Usage: kinnoo init <agent-name>", file=sys.stderr)
            sys.exit(1)
        if not re.match(NAME_PATTERN, args.agent_name):
            print(f"Error: Invalid agent name '{args.agent_name}'. Must match pattern: {NAME_PATTERN}", file=sys.stderr)
            sys.exit(1)
        from kinnoo.init_command import init_agent
        from pathlib import Path
        try:
            init_agent(args.agent_name, Path.cwd())
            print(f"Initialized agent: {args.agent_name}")
        except FileExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "run":
        agent_dir = Path(args.agent_dir)
        venv_dir = agent_dir / ".venv"
        requirements = agent_dir / "requirements.txt"
        # Ensure .venv exists (task8, assumed done)
        if not venv_dir.exists():
            import venv
            venv.create(venv_dir, with_pip=True)
        # Install requirements.txt packages into venv
        if requirements.exists() and requirements.read_text().strip():
            pip_exe = venv_dir / "bin" / "pip"
            if not pip_exe.exists():
                pip_exe = venv_dir / "Scripts" / "pip.exe"  # Windows fallback
            if not pip_exe.exists():
                print(f"Error: pip not found in venv at {pip_exe}", file=sys.stderr)
                sys.exit(1)
            import subprocess
            result = subprocess.run([str(pip_exe), "install", "-r", str(requirements)], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error installing requirements:\n{result.stderr}", file=sys.stderr)
                sys.exit(result.returncode)
            else:
                print(result.stdout)

if __name__ == "__main__":
    main()
