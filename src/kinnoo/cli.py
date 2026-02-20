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

if __name__ == "__main__":
    main()
