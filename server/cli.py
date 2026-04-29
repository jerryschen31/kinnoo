"""CLI entrypoint for remote registry server utilities."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import secrets
import subprocess
import sys

from server.bootstrap import bootstrap_admin
from server.database.repository import RegistryRepository
from server.database.session import create_database_runtime, ping_database
from server.metadata.models import VersionMetadata, utc_now_iso
from server.metadata.postgres_manager import PostgresMetadataManager
from server.models.user import username_to_tenant_slug
from server.storage.user_store import UserStore


def _generate_temporary_password() -> str:
    return secrets.token_urlsafe(16)


def _build_store(store_root: str) -> UserStore:
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    return UserStore(root)


def _is_locked(locked_until: str | None) -> bool:
    if not locked_until:
        return False
    try:
        lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
    except ValueError:
        return False
    return lock_time > datetime.now(timezone.utc)


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

    user_parser = subparsers.add_parser("user", help="User administration commands")
    user_subparsers = user_parser.add_subparsers(dest="user_command")

    user_create = user_subparsers.add_parser("create", help="Create a user with a temporary password")
    user_create.add_argument("--store-root", default=".", help="Filesystem root for server persistence.")
    user_create.add_argument("--email", required=True, help="Email address for the user.")
    user_create.add_argument(
        "--role",
        choices=["admin", "user"],
        default="user",
        help="Role for the created user (default: user).",
    )

    user_list = user_subparsers.add_parser("list", help="List users")
    user_list.add_argument("--store-root", default=".", help="Filesystem root for server persistence.")

    user_reset = user_subparsers.add_parser(
        "reset-password", help="Reset a user's password and print a new temporary password"
    )
    user_reset.add_argument("--store-root", default=".", help="Filesystem root for server persistence.")
    user_reset.add_argument("--email", required=True, help="Email of the user to reset.")

    user_unlock = user_subparsers.add_parser("unlock", help="Clear lockout state for a user")
    user_unlock.add_argument("--store-root", default=".", help="Filesystem root for server persistence.")
    user_unlock.add_argument("--email", required=True, help="Email of the user to unlock.")

    user_delete = user_subparsers.add_parser("delete", help="Delete a user")
    user_delete.add_argument("--store-root", default=".", help="Filesystem root for server persistence.")
    user_delete.add_argument("--email", required=True, help="Email of the user to delete.")
    user_delete.add_argument("--force", action="store_true", help="Delete without interactive confirmation.")

    invite_parser = subparsers.add_parser("invite", help="Invite token commands")
    invite_subparsers = invite_parser.add_subparsers(dest="invite_command")

    invite_create = invite_subparsers.add_parser("create", help="Create an invite token")
    invite_create.add_argument("--store-root", default=".", help="Filesystem root for server persistence.")
    invite_create.add_argument("--email", required=True, help="Email address for the invite.")
    invite_create.add_argument(
        "--days-valid",
        type=int,
        default=7,
        help="Number of days the invite remains valid (default: 7).",
    )

    invite_list = invite_subparsers.add_parser("list", help="List invite tokens")
    invite_list.add_argument("--store-root", default=".", help="Filesystem root for server persistence.")

    db_parser = subparsers.add_parser("db", help="Postgres database operations")
    db_subparsers = db_parser.add_subparsers(dest="db_command")

    db_migrate = db_subparsers.add_parser("migrate", help="Run alembic migrations to head")
    db_migrate.add_argument(
        "--database-url",
        default=(os.getenv("REGISTRY_DATABASE_URL") or "").strip(),
        help="Postgres connection URL (defaults to REGISTRY_DATABASE_URL).",
    )

    db_seed = db_subparsers.add_parser("seed", help="Seed a sample tenant/agent/version in Postgres")
    db_seed.add_argument(
        "--database-url",
        default=(os.getenv("REGISTRY_DATABASE_URL") or "").strip(),
        help="Postgres connection URL (defaults to REGISTRY_DATABASE_URL).",
    )
    db_seed.add_argument("--tenant-slug", default="seed-tenant")
    db_seed.add_argument("--agent-slug", default="seed-agent")
    db_seed.add_argument("--version", default="0.1.0")

    db_list = db_subparsers.add_parser("list", help="List db domain records")
    db_list.add_argument(
        "resource",
        choices=["tenants", "users", "agents", "audit"],
        help="Domain resource to list.",
    )
    db_list.add_argument(
        "--database-url",
        default=(os.getenv("REGISTRY_DATABASE_URL") or "").strip(),
        help="Postgres connection URL (defaults to REGISTRY_DATABASE_URL).",
    )
    db_list.add_argument("--limit", type=int, default=20, help="Limit for audit listing.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "bootstrap":
        result = bootstrap_admin(store_root=Path(args.store_root), username=args.username)
        if not result.created:
            print(result.message, file=sys.stderr)
            return 1
        print(result.message)
        print(f"username: {result.username}")
        print(f"temporary password: {result.temporary_password}")
        return 0

    if args.command == "user":
        if args.user_command is None:
            parser.print_help(sys.stderr)
            return 2
        store = _build_store(args.store_root)

        if args.user_command == "create":
            password = _generate_temporary_password()
            role = "admin" if args.role == "admin" else "user"
            try:
                user = store.create_user(username=args.email, plaintext_password=password, role=role)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(f"created user: {user.username}")
            print(f"role: {user.role}")
            print(f"temporary password: {password}")
            return 0

        if args.user_command == "list":
            users = store.list_users()
            if not users:
                print("no users found")
                return 0
            print("EMAIL\tSTATUS\tTENANT\tCREATED")
            for user in users:
                status = "locked" if _is_locked(user.locked_until) else "active"
                created = user.created_at.split("T", 1)[0] if "T" in user.created_at else user.created_at
                tenant_slug = username_to_tenant_slug(user.username)
                print(f"{user.username}\t{status}\t{tenant_slug}\t{created}")
            return 0

        if args.user_command == "reset-password":
            password = _generate_temporary_password()
            try:
                store.reset_password(email=args.email, new_password=password)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(f"password reset for: {args.email}")
            print(f"temporary password: {password}")
            return 0

        if args.user_command == "unlock":
            try:
                store.unlock_user(email=args.email)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            print(f"unlocked user: {args.email}")
            return 0

        if args.user_command == "delete":
            if not args.force:
                answer = input(f"Delete user '{args.email}'? [y/N]: ").strip().lower()
                if answer not in {"y", "yes"}:
                    print("aborted")
                    return 1
            if not store.delete_user(email=args.email):
                print(f"User not found for email '{args.email}'.", file=sys.stderr)
                return 1
            print(f"deleted user: {args.email}")
            return 0

    if args.command == "invite":
        if args.invite_command is None:
            parser.print_help(sys.stderr)
            return 2
        store = _build_store(args.store_root)

        if args.invite_command == "create":
            try:
                invite = store.create_invite(email=args.email, days_valid=args.days_valid)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            base_url = os.getenv("KINNOO_PUBLIC_BASE_URL", "http://localhost:3000").rstrip("/")
            print(f"invite token: {invite['token']}")
            print(f"url: {base_url}/register?token={invite['token']}")
            print(f"expires: {invite['expires_at']}")
            return 0

        if args.invite_command == "list":
            invites = store.list_invites()
            if not invites:
                print("no invites found")
                return 0
            print("EMAIL\tTOKEN\tEXPIRES\tSTATUS")
            for invite in invites:
                token = str(invite.get("token", ""))
                short_token = f"{token[:7]}..." if len(token) > 10 else token
                status = "consumed" if bool(invite.get("consumed", False)) else "pending"
                print(f"{invite.get('email', '')}\t{short_token}\t{invite.get('expires_at', '')}\t{status}")
            return 0

    if args.command == "db":
        if args.db_command is None:
            parser.print_help(sys.stderr)
            return 2
        if not args.database_url:
            print("Database URL is required. Set --database-url or REGISTRY_DATABASE_URL.", file=sys.stderr)
            return 1
        runtime = create_database_runtime(
            database_url=args.database_url,
            pool_size=5,
            max_overflow=5,
            pool_recycle_seconds=1800,
        )
        repository = RegistryRepository(session_factory=runtime.sync_session_factory)
        manager = PostgresMetadataManager(repository=repository)
        try:
            ping_database(runtime.sync_engine)
        except Exception as exc:
            print(f"Database connection failed: {exc}", file=sys.stderr)
            return 1

        if args.db_command == "migrate":
            migration_ini = Path(__file__).parent / "database" / "migrations" / "alembic.ini"
            command = [
                sys.executable,
                "-m",
                "alembic",
                "-c",
                str(migration_ini),
                "upgrade",
                "head",
            ]
            env = dict(os.environ)
            env["REGISTRY_DATABASE_URL"] = args.database_url
            result = subprocess.run(command, text=True, capture_output=True, check=False, env=env)
            if result.returncode != 0:
                message = (result.stdout or "") + (result.stderr or "")
                print(message.strip(), file=sys.stderr)
                return 1
            print("Database migration completed: head")
            return 0

        if args.db_command == "seed":
            now = utc_now_iso()
            metadata = VersionMetadata(
                tenant_slug=args.tenant_slug,
                agent_slug=args.agent_slug,
                version=args.version,
                visibility="private",
                manifest={"name": args.agent_slug, "version": args.version},
                storage_keys={"archive": f"archives/{args.tenant_slug}/{args.agent_slug}/{args.version}.kno"},
                integrity={"sha256": "seed"},
                publisher={"user_id": "seed-cli"},
                created_at=now,
                updated_at=now,
            )
            manager.upsert_version_metadata(metadata)
            print(f"Seeded metadata for {args.tenant_slug}/{args.agent_slug}@{args.version}")
            return 0

        if args.db_command == "list":
            if args.resource == "tenants":
                rows = repository.list_tenants()
            elif args.resource == "users":
                rows = repository.list_users()
            elif args.resource == "agents":
                rows = repository.list_agents()
            else:
                rows = repository.list_audit_log(limit=args.limit)
            if not rows:
                print("no records found")
                return 0
            for row in rows:
                print(row)
            return 0

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
