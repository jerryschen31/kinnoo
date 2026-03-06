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
    from kinnoo import __version__ as KINNOO_VERSION
except ImportError:
    # fallback for direct script execution
    from .schema import NAME_PATTERN
    from . import __version__ as KINNOO_VERSION

def main():
    import os
    parser = argparse.ArgumentParser(prog="kinnoo", description="Kinnoo CLI")
    parser.add_argument("--version", action="version", version=KINNOO_VERSION)
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

    # Add 'install' subcommand
    install_parser = subparsers.add_parser("install", help="Install a kinnoo agent archive (.kno)")
    install_parser.add_argument("archive_path", nargs="?", help="Path to .kno archive to install")
    install_parser.add_argument("target_dir", nargs="?", help="(Optional) Directory to extract agent to")

    # Add 'pack' subcommand
    pack_parser = subparsers.add_parser("pack", help="Package an agent directory into a .kno archive")
    pack_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory to package")
    pack_parser.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        help="(Optional) Increment manifest version before packaging",
    )

    # Add 'inspect' subcommand
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect metadata from an agent directory or .kno archive",
    )
    inspect_parser.add_argument(
        "target",
        nargs="?",
        help="Path to agent directory or .kno archive",
    )

    # Add 'publish' subcommand
    publish_parser = subparsers.add_parser(
        "publish",
        help="Publish latest archived agent artifact to the registry",
    )
    publish_parser.add_argument(
        "agent_name",
        nargs="?",
        help="Agent name to publish from local archive source",
    )
    publish_parser.add_argument(
        "--local",
        action="store_true",
        help="Explicitly select the local registry backend",
    )

    # Add 'list' subcommand
    list_parser = subparsers.add_parser(
        "list",
        help="List agents from local archive (default) or remote registry",
    )
    list_source_group = list_parser.add_mutually_exclusive_group()
    list_source_group.add_argument(
        "--local",
        action="store_true",
        help="List agents from local archive source (default)",
    )
    list_source_group.add_argument(
        "--remote",
        action="store_true",
        help="List agents from remote mock registry source",
    )

    # Add 'search' subcommand
    search_parser = subparsers.add_parser(
        "search",
        help="Search locally published registry agents",
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        help="Search query to match against agent name and description",
    )

    # Pre-parse sys.argv for missing args to print custom usage before argparse error
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        if "-h" not in sys.argv and "--help" not in sys.argv and len(sys.argv) < 4:
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

        try:
            from kinnoo.run_command import run_agent
        except ImportError:
            from .run_command import run_agent

        exit_code = run_agent(agent_dir_arg=args.agent_dir, input_arg=args.input)
        sys.exit(exit_code)

    elif args.command == "install":
        archive_path = getattr(args, "archive_path", None)
        target_dir_arg = getattr(args, "target_dir", None)
        if archive_path is None:
            print("Usage: kinnoo install <archive-path> [target-dir]", file=sys.stderr)
            sys.exit(1)
        force = False
        if hasattr(args, "force"):
            force = args.force
        if "--force" in sys.argv:
            force = True
        try:
            from kinnoo.install_command import install_agent
        except ImportError:
            from .install_command import install_agent

        exit_code = install_agent(archive_path=archive_path, target_dir_arg=target_dir_arg, force=force)
        sys.exit(exit_code)

    elif args.command == "pack":
        agent_dir = args.agent_dir
        if agent_dir is None:
            print("Usage: kinnoo pack <agent-dir>")
            sys.exit(1)
        try:
            from kinnoo.pack_command import pack_agent
        except ImportError:
            from .pack_command import pack_agent

        exit_code = pack_agent(agent_dir, bump=getattr(args, "bump", None))
        sys.exit(exit_code)

    elif args.command == "inspect":
        target = getattr(args, "target", None)
        if target is None:
            print("Usage: kinnoo inspect <target>", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.inspect_command import inspect_target
        except ImportError:
            from .inspect_command import inspect_target

        exit_code = inspect_target(target)
        sys.exit(exit_code)

    elif args.command == "publish":
        agent_name = getattr(args, "agent_name", None)
        if agent_name is None:
            print("Usage: kinnoo publish <agent-name> [--local]", file=sys.stderr)
            sys.exit(1)

        use_local = bool(getattr(args, "local", False))

        try:
            from kinnoo.publish_command import publish_agent
        except ImportError:
            from .publish_command import publish_agent

        exit_code = publish_agent(agent_name=agent_name, use_local=use_local)
        sys.exit(exit_code)

    elif args.command == "list":
        source = "remote" if bool(getattr(args, "remote", False)) else "local"

        try:
            from kinnoo.list_command import list_agents
        except ImportError:
            from .list_command import list_agents

        exit_code = list_agents(source=source)
        sys.exit(exit_code)

    elif args.command == "search":
        query = getattr(args, "query", None)
        if query is None:
            print("Usage: kinnoo search <query>", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.search_command import search_agents
        except ImportError:
            from .search_command import search_agents

        exit_code = search_agents(query)
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
