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


RUN_USAGE_TEXT = (
    "Usage: kinnoo run <agent-dir> '<input>'\n"
    "       kinnoo run <agent-dir>\n"
    "       kinnoo run <agent-dir> --json-input '<json>'\n"
    "       kinnoo run <agent-dir> --json-file <json-file>\n"
    "       kinnoo run <agent-dir> -- <args...>"
)

IMPORT_USAGE_TEXT = "Usage: kinnoo import [path]"


class KinnooArgumentParser(argparse.ArgumentParser):
    """ArgumentParser variant that prints description before usage in help output."""

    def format_help(self) -> str:
        formatter = self._get_formatter()

        if self.description:
            formatter.add_text(self.description)

        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        formatter.add_text(self.epilog)
        return formatter.format_help()

def main():
    import os
    parser = KinnooArgumentParser(prog="kinnoo", description="Kinnoo CLI")
    parser.add_argument("--version", action="version", version=KINNOO_VERSION)
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=KinnooArgumentParser,
    )

    # init subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Scaffold a new kinnoo agent",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Scaffold a new kinnoo agent",
        epilog=(
            "Examples:\n"
            "  kinnoo init my-agent\n"
            "  kinnoo init --framework claude-chat my-claude-agent\n"
            "  kinnoo init --framework openclaw my-openclaw-agent \n"
            "  kinnoo init --framework mcp-client  my-mcp-client\n"
            "  kinnoo init --framework mcp-server my-mcp-server"
        ),
    )
    init_parser.add_argument("agent_name", nargs="?", help="Name of the agent to create")
    init_parser.add_argument(
        "--framework",
        choices=["gemini", "chatgpt", "claude-chat", "pydantic-ai", "langgraph", "openai-agents", "mcp-client", "mcp-server", "openclaw"],
        help=(
            "(Optional) Pre-populate agent with LLM framework template "
            "(gemini, chatgpt, claude-chat, pydantic-ai, langgraph, openai-agents, mcp-client, mcp-server, openclaw)"
        )
    )

    # Add 'run' subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Run a kinnoo agent",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Run a kinnoo agent",
        epilog=(
            "Examples:\n"
            "  kinnoo run <agent-dir> '<input>'\n"
            "  kinnoo run <agent-dir>\n"
            "  kinnoo run <agent-dir> --json-input '{\"task\":\"ping\"}'\n"
            "  kinnoo run <agent-dir> --json-file ./payload.json\n"
            "  kinnoo run <agent-dir> -- -e <some-string> -p <some-file-path> -u <some-url>"
        ),
    )
    run_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory")
    run_parser.add_argument(
        "input",
        nargs="?",
        help=(
            "Optional input string to pass to the agent entrypoint. "
            "May be omitted for agents that accept no input, and is not required when --json-input or --json-file is used."
        ),
    )
    run_parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run readiness checks only; do not execute the agent entrypoint",
    )
    run_parser.add_argument(
        "--no-guard",
        action="store_true",
        help="Disable input safety check for CI/automation pipelines",
    )
    run_parser.add_argument(
        "--json-input",
        dest="json_input",
        help="Inline JSON payload for agents expecting structured input",
    )
    run_parser.add_argument(
        "--json-file",
        dest="json_file",
        help="Path to a JSON file payload for agents expecting structured input",
    )
    run_parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Run agent with manifest permission policy enforcement",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show predicted runtime behavior without executing full entrypoint side effects",
    )
    run_parser.add_argument(
        "--max-seconds",
        type=float,
        help=(
            "Wall-clock timeout in seconds for run execution. "
            "If omitted, no wall-clock timeout is enforced by this option."
        ),
    )
    run_parser.add_argument(
        "--max-cpu-seconds",
        type=int,
        help=(
            "CPU time budget in seconds for supported platforms. "
            "If omitted, no CPU-time budget is enforced by this option."
        ),
    )
    run_parser.add_argument(
        "--max-memory-mb",
        type=int,
        help=(
            "Memory budget in MB for supported platforms. "
            "If omitted, no memory budget is enforced by this option."
        ),
    )

    # Add 'stop' subcommand
    stop_parser = subparsers.add_parser(
        "stop",
        help="Stop a running daemon agent",
        description="Stop a running daemon agent",
    )
    stop_parser.add_argument("agent_dir", nargs="?", help="Path to daemon agent directory")

    # Add 'attach' subcommand
    attach_parser = subparsers.add_parser(
        "attach",
        help="Attach to a running daemon agent session",
        description="Attach to a running daemon agent session",
    )
    attach_parser.add_argument("agent_dir", nargs="?", help="Path to daemon agent directory")

    # Add 'logs' subcommand
    logs_parser = subparsers.add_parser(
        "logs",
        help="Show daemon logs (tail or follow)",
        description="Show daemon logs (tail or follow)",
    )
    logs_parser.add_argument("agent_dir", nargs="?", help="Path to daemon agent directory")
    logs_parser.add_argument(
        "--follow",
        action="store_true",
        help="Stream new log lines until daemon exits or operator interrupts",
    )
    logs_parser.add_argument(
        "--tail",
        type=int,
        default=20,
        help="Number of recent lines to show before follow/tail output (default: 20)",
    )

    # Add 'install' subcommand
    install_parser = subparsers.add_parser(
        "install",
        help="Install a kinnoo agent from archive (.kno) or registry",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Install a kinnoo agent from archive (.kno) or registry",
        epilog=(
            "Examples:\n"
            "  kinnoo install ./dist/my-agent-0.1.0.kno\n"
            "  kinnoo install ./dist/my-agent-0.1.0.kno ./agents/my-agent\n"
            "  kinnoo install my-agent==1.2.0 --remote\n"
            "  kinnoo install ./dist/my-openclaw-agent-0.3.0.kno --ignore-scripts --allow-vulnerable"
        ),
    )
    install_parser.add_argument(
        "archive_path",
        nargs="?",
        metavar="agent[==version]",
        help=(
            "agent name from registry (use kinnoo list / search to find available agents)\n"
            "OR specify a direct path to a local .kno archive"
        ),
    )
    install_parser.add_argument("target_dir", nargs="?", help="(Optional) Directory to extract agent to")
    install_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip install confirmation prompt (shows summary and proceeds)",
    )
    install_parser.add_argument(
        "--state-overwrite",
        action="store_true",
        help="Allow state snapshot restore to overwrite existing extracted state directories (commonly used by OpenClaw/stateful agents)",
    )

    openclaw_install_group = install_parser.add_argument_group(
        "OpenClaw/Node-focused install options"
    )
    openclaw_install_group.add_argument(
        "--allow-vulnerable",
        action="store_true",
        help="(OpenClaw/Node-focused) Allow install to continue when Node audit reports critical vulnerabilities (security risk)",
    )
    openclaw_install_group.add_argument(
        "--ignore-scripts",
        action="store_true",
        help="(OpenClaw/Node-focused) Disable Node package lifecycle scripts during dependency installation",
    )
    install_parser.add_argument(
        "--accept-permissions",
        action="store_true",
        help="Acknowledge and accept declared manifest permissions during non-interactive install",
    )
    install_parser.add_argument(
        "--allow-unverified-publisher",
        action="store_true",
        help="Allow non-interactive install when archive has no publisher signature metadata",
    )
    install_source_group = install_parser.add_mutually_exclusive_group()
    install_source_group.add_argument(
        "--local",
        action="store_true",
        help="Force local registry backend resolution for registry install targets",
    )
    install_source_group.add_argument(
        "--remote",
        action="store_true",
        help="Force remote registry backend resolution for registry install targets",
    )

    # Add 'pack' subcommand
    pack_parser = subparsers.add_parser("pack", help="Package an agent directory into a .kno archive")
    pack_parser.description = "Package an agent directory into a .kno archive"
    pack_parser.formatter_class = argparse.RawTextHelpFormatter
    pack_parser.epilog = (
        "Examples:\n"
        "  kinnoo pack ./my-agent\n"
        "  kinnoo pack ./my-agent --bump patch\n"
        "  kinnoo pack ./my-agent --sign --signing-key ./keys/kinnoo-ed25519-private.pem"
    )
    pack_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory to package")
    pack_parser.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        help="(Optional) Increment manifest version before packaging",
    )
    pack_parser.add_argument(
        "--sign",
        action="store_true",
        help="Sign packaged archive and emit detached signature artifacts",
    )
    pack_parser.add_argument(
        "--signing-key",
        help="Path to Ed25519 private key PEM used with --sign",
    )

    # Add 'keygen' subcommand
    keygen_parser = subparsers.add_parser(
        "keygen",
        help="Generate an Ed25519 keypair for archive signing",
        description="Generate an Ed25519 keypair for archive signing",
    )
    keygen_parser.add_argument(
        "--private-key",
        default="kinnoo-ed25519-private.pem",
        help="Path for private key PEM output (default: kinnoo-ed25519-private.pem)",
    )
    keygen_parser.add_argument(
        "--public-key",
        default="kinnoo-ed25519-public.pem",
        help="Path for public key PEM output (default: kinnoo-ed25519-public.pem)",
    )

    # Add 'inspect' subcommand
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect metadata from an agent directory or .kno archive",
        description="Inspect metadata from an agent directory or .kno archive",
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
        formatter_class=argparse.RawTextHelpFormatter,
        description="Publish latest archived agent artifact to the registry",
        epilog=(
            "Examples:\n"
            "  kinnoo publish my-agent --local\n"
            "  kinnoo publish my-agent --remote\n"
            "  kinnoo publish ./dist/my-agent-1.0.0.kno --remote\n"
            "  kinnoo publish ./my-agent --pack --bump minor --remote"
        ),
    )
    publish_parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Agent name (default archive-first mode), .kno path, or with --pack "
            "a file path to an agent directory"
        ),
    )
    publish_parser.add_argument(
        "--local",
        action="store_true",
        help="Explicitly select the local registry backend",
    )
    publish_parser.add_argument(
        "--remote",
        action="store_true",
        help="Explicitly select the remote registry backend",
    )
    publish_parser.add_argument(
        "--pack",
        action="store_true",
        help="Pack first, then publish. With --pack, <target> must be a file path to an agent directory.",
    )
    publish_parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Optional version bump applied during --pack flow before publish.",
    )

    # Add 'list' subcommand
    list_parser = subparsers.add_parser(
        "list",
        help="List agents from local archive (default) or remote registry",
        description="List agents from local archive (default) or remote registry",
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
        help="Search agents from local archive (default) or remote registry",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Search agents from local archive (default) or remote registry",
        epilog=(
            "Examples:\n"
            "  kinnoo search writer\n"
            "  kinnoo search mcp --local\n"
            "  kinnoo search openclaw --remote"
        ),
    )
    search_source_group = search_parser.add_mutually_exclusive_group()
    search_source_group.add_argument(
        "--local",
        action="store_true",
        help="Search agents from local archive source (default)",
    )
    search_source_group.add_argument(
        "--remote",
        action="store_true",
        help="Search agents from remote mock registry source",
    )
    search_parser.add_argument(
        "query",
        nargs="?",
        help="Search query to match against agent name and description",
    )

    # Add 'import' subcommand
    import_parser = subparsers.add_parser(
        "import",
        help="Import an existing project in-place and prepare kinnoo metadata",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Import an existing project in-place and prepare kinnoo metadata",
        epilog=(
            "Examples:\n"
            "  kinnoo import\n"
            "  kinnoo import ./existing-project --force"
        ),
    )
    import_parser.add_argument(
        "path",
        nargs="?",
        help="(Optional) Path to existing project directory (defaults to current directory)",
    )
    import_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing kinnoo.yaml in target directory",
    )

    # Pre-parse sys.argv for missing args to print custom usage before argparse error
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        if (
            "-h" not in sys.argv
            and "--help" not in sys.argv
            and "--preflight" not in sys.argv
            and "--no-guard" not in sys.argv
            and len(sys.argv) < 3
        ):
            print(RUN_USAGE_TEXT, file=sys.stderr)
            sys.exit(1)

    run_pass_through_args: list[str] = []
    if len(sys.argv) > 1 and sys.argv[1] == "run" and "--" in sys.argv:
        separator_index = sys.argv.index("--")
        run_pass_through_args = sys.argv[separator_index + 1 :]
        args = parser.parse_args(sys.argv[1:separator_index])
    else:
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
        preflight_mode = bool(getattr(args, "preflight", False))
        input_arg = args.input
        pass_through_args = run_pass_through_args
        if not hasattr(args, "agent_dir") or args.agent_dir is None:
            if preflight_mode:
                print("Usage: kinnoo run <agent-dir> --preflight", file=sys.stderr)
            else:
                print(RUN_USAGE_TEXT, file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.run_command import run_agent
        except ImportError:
            from .run_command import run_agent

        exit_code = run_agent(
            agent_dir_arg=args.agent_dir,
            input_arg=input_arg,
            json_input_arg=getattr(args, "json_input", None),
            json_file_arg=getattr(args, "json_file", None),
            preflight=preflight_mode,
            no_guard=bool(getattr(args, "no_guard", False)),
            pass_through_args=pass_through_args,
            sandbox=bool(getattr(args, "sandbox", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
            max_seconds=getattr(args, "max_seconds", None),
            max_cpu_seconds=getattr(args, "max_cpu_seconds", None),
            max_memory_mb=getattr(args, "max_memory_mb", None),
        )
        sys.exit(exit_code)

    elif args.command == "install":
        archive_path = getattr(args, "archive_path", None)
        target_dir_arg = getattr(args, "target_dir", None)
        if archive_path is None:
            print(
                "Usage: kinnoo install <archive-path | agent_name[==version]> [target-dir]",
                file=sys.stderr,
            )
            sys.exit(1)
        force = False
        if hasattr(args, "force"):
            force = args.force
        if "--force" in sys.argv:
            force = True
        assume_yes = bool(getattr(args, "yes", False))
        overwrite_state = bool(getattr(args, "state_overwrite", False))
        allow_vulnerable = bool(getattr(args, "allow_vulnerable", False))
        ignore_scripts = bool(getattr(args, "ignore_scripts", False))
        accept_permissions = bool(getattr(args, "accept_permissions", False))
        allow_unverified_publisher = bool(getattr(args, "allow_unverified_publisher", False))
        use_local = bool(getattr(args, "local", False))
        use_remote = bool(getattr(args, "remote", False))
        try:
            from kinnoo.install_command import install_agent
        except ImportError:
            from .install_command import install_agent

        exit_code = install_agent(
            archive_path=archive_path,
            target_dir_arg=target_dir_arg,
            force=force,
            assume_yes=assume_yes,
            overwrite_state=overwrite_state,
            allow_vulnerable=allow_vulnerable,
            ignore_scripts=ignore_scripts,
            accept_permissions=accept_permissions,
            allow_unverified_publisher=allow_unverified_publisher,
            use_local=use_local,
            use_remote=use_remote,
        )
        sys.exit(exit_code)

    elif args.command == "stop":
        agent_dir = getattr(args, "agent_dir", None)
        if agent_dir is None:
            print("Usage: kinnoo stop <agent-dir>", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.run_command import stop_agent
        except ImportError:
            from .run_command import stop_agent

        exit_code = stop_agent(agent_dir)
        sys.exit(exit_code)

    elif args.command == "attach":
        agent_dir = getattr(args, "agent_dir", None)
        if agent_dir is None:
            print("Usage: kinnoo attach <agent-dir>", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.run_command import attach_agent
        except ImportError:
            from .run_command import attach_agent

        exit_code = attach_agent(agent_dir)
        sys.exit(exit_code)

    elif args.command == "logs":
        agent_dir = getattr(args, "agent_dir", None)
        if agent_dir is None:
            print("Usage: kinnoo logs <agent-dir> [--tail N] [--follow]", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.run_command import logs_agent
        except ImportError:
            from .run_command import logs_agent

        exit_code = logs_agent(
            agent_dir_arg=agent_dir,
            follow=bool(getattr(args, "follow", False)),
            tail_lines=int(getattr(args, "tail", 20)),
        )
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

        exit_code = pack_agent(
            agent_dir,
            bump=getattr(args, "bump", None),
            sign=bool(getattr(args, "sign", False)),
            signing_key_path=getattr(args, "signing_key", None),
        )
        sys.exit(exit_code)

    elif args.command == "keygen":
        private_key_path = Path(getattr(args, "private_key"))
        public_key_path = Path(getattr(args, "public_key"))

        if private_key_path.resolve() == public_key_path.resolve():
            print("Error: --private-key and --public-key must be different paths", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.signing import generate_ed25519_keypair
        except ImportError:
            from .signing import generate_ed25519_keypair

        try:
            result = generate_ed25519_keypair(
                private_key_path=private_key_path,
                public_key_path=public_key_path,
            )
        except (OSError, ValueError) as exc:
            print(f"Error: Failed to generate keypair: {exc}", file=sys.stderr)
            sys.exit(1)

        print("[kinnoo keygen] Generated Ed25519 keypair.")
        print(f"[kinnoo keygen] Private key: {result.private_key_path}")
        print(f"[kinnoo keygen] Public key: {result.public_key_path}")
        print(f"[kinnoo keygen] Public key fingerprint (SHA256): {result.public_key_fingerprint}")
        sys.exit(0)

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
        target = getattr(args, "target", None)
        if target is None:
            print(
                "Usage: kinnoo publish <agent-name|archive.kno|agent-dir-path> "
                "[--pack] [--bump {major,minor,patch}] [--local|--remote]",
                file=sys.stderr,
            )
            sys.exit(1)

        use_local = bool(getattr(args, "local", False))
        use_remote = bool(getattr(args, "remote", False))
        use_pack = bool(getattr(args, "pack", False))
        bump = getattr(args, "bump", None)

        if use_local and use_remote:
            print("Error: --local and --remote cannot be used together.", file=sys.stderr)
            sys.exit(1)

        if bump is not None and not use_pack:
            print("Error: --bump can only be used together with --pack.", file=sys.stderr)
            sys.exit(1)

        try:
            from kinnoo.publish_command import publish_agent
        except ImportError:
            from .publish_command import publish_agent

        exit_code = publish_agent(
            target=target,
            use_local=use_local,
            use_remote=use_remote,
            pack=use_pack,
            bump=bump,
        )
        sys.exit(exit_code)

    elif args.command == "list":
        if bool(getattr(args, "local", False)):
            source = "local"
        elif bool(getattr(args, "remote", False)):
            source = "remote"
        else:
            source = "auto"

        try:
            from kinnoo.list_command import list_agents
        except ImportError:
            from .list_command import list_agents

        exit_code = list_agents(source=source)
        sys.exit(exit_code)

    elif args.command == "search":
        query = getattr(args, "query", None)
        if query is None:
            print("Usage: kinnoo search [--local | --remote] <query>", file=sys.stderr)
            sys.exit(1)

        if bool(getattr(args, "local", False)):
            source = "local"
        elif bool(getattr(args, "remote", False)):
            source = "remote"
        else:
            source = "auto"

        try:
            from kinnoo.search_command import search_agents
        except ImportError:
            from .search_command import search_agents

        exit_code = search_agents(query=query, source=source)
        sys.exit(exit_code)

    elif args.command == "import":
        target_path_arg = getattr(args, "path", None)
        force = bool(getattr(args, "force", False))

        try:
            from kinnoo.import_command import import_agent
        except ImportError:
            from .import_command import import_agent

        exit_code = import_agent(target_path_arg=target_path_arg, force=force)
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
