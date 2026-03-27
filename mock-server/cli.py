"""CLI entrypoint for remote registry server utilities."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from server.bootstrap import bootstrap_admin


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kinnoo-server")
    subparsers = parser.add_subparsers(dest="command")

    bootstrap_parser = subparsers.add_parser("bootstrap", help="Create first admin account")
    bootstrap_parser.add_argument(
        "--store-root",
        default=".",
        help="Filesystem root for server persistence (default: current directory).",
    )
    bootstrap_parser.add_argument(
        "--username",
        default="admin",
        help="Admin username to create (default: admin).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command != "bootstrap":
        parser.print_help(sys.stderr)
        return 2

    result = bootstrap_admin(store_root=Path(args.store_root), username=args.username)
    if not result.created:
        print(result.message, file=sys.stderr)
        return 1

    # Print temporary password exactly once to stdout for operator capture.
    print(result.message)
    print(f"username: {result.username}")
    print(f"temporary password: {result.temporary_password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
