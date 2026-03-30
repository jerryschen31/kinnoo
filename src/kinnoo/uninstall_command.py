from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

try:
    from kinnoo.config import resolve_lockfile_path
    from kinnoo.install_trace import write_uninstall_trace
except ImportError:
    from .config import resolve_lockfile_path
    from .install_trace import write_uninstall_trace


DEFAULT_AGENT_INSTALL_ROOT = Path.home() / ".kinnoo" / "agents"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_agent_install_root() -> Path:
    override = DEFAULT_AGENT_INSTALL_ROOT
    env_value = os.environ.get("KINNOO_AGENT_INSTALL_ROOT", "").strip()
    if env_value:
        try:
            return Path(env_value).expanduser().resolve()
        except OSError:
            return Path(env_value).expanduser()
    return override


def _remove_agent_from_lockfile(*, agent_name: str, install_root: Path) -> tuple[bool, str | None]:
    lockfile_path = resolve_lockfile_path(start_dir=install_root)
    if not lockfile_path.exists() or not lockfile_path.is_file():
        return False, None

    try:
        lockfile_doc = yaml.safe_load(lockfile_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        return False, f"failed to read lockfile '{lockfile_path}': {error}"

    if not isinstance(lockfile_doc, dict):
        return False, f"lockfile '{lockfile_path}' is not a valid mapping"

    agents = lockfile_doc.get("agents")
    if not isinstance(agents, dict):
        return False, f"lockfile '{lockfile_path}' is missing an 'agents' mapping"

    if agent_name not in agents:
        return False, None

    del agents[agent_name]
    ordered_agents: dict[str, object] = {}
    for key in sorted(agents.keys()):
        ordered_agents[str(key)] = agents[key]

    lockfile_doc["agents"] = ordered_agents
    lockfile_doc["locked_at"] = _utc_now_iso()

    try:
        lockfile_path.write_text(
            yaml.safe_dump(lockfile_doc, sort_keys=False),
            encoding="utf-8",
        )
    except OSError as error:
        return False, f"failed to write lockfile '{lockfile_path}': {error}"

    return True, None


def uninstall_agent(agent_name: str, install_root_arg: str | None = None) -> int:
    normalized_name = agent_name.strip()
    if not normalized_name:
        print("Error: uninstall requires a non-empty agent name.", file=sys.stderr)
        return 1

    if install_root_arg:
        install_root = Path(install_root_arg).expanduser().resolve()
    else:
        install_root = resolve_agent_install_root()

    target_dir = install_root / normalized_name
    if not target_dir.exists() or not target_dir.is_dir():
        print(
            f"Error: Installed agent '{normalized_name}' was not found at '{target_dir}'.",
            file=sys.stderr,
        )
        print(
            "Error: Install the agent first or verify KINNOO_AGENT_INSTALL_ROOT before uninstall.",
            file=sys.stderr,
        )
        return 1

    try:
        confirmation = input(
            f"Confirm uninstall of '{normalized_name}' at '{target_dir}'? [y/N]: "
        ).strip().lower()
    except EOFError:
        print("Uninstall aborted by user.", file=sys.stderr)
        return 1

    if confirmation not in {"y", "yes"}:
        print("Uninstall aborted by user.", file=sys.stderr)
        return 1

    try:
        shutil.rmtree(target_dir)
    except Exception as error:
        print(
            f"Error: Failed to remove installed agent directory '{target_dir}': {error}",
            file=sys.stderr,
        )
        return 1

    removed_from_lockfile, lockfile_error = _remove_agent_from_lockfile(
        agent_name=normalized_name,
        install_root=install_root,
    )
    if lockfile_error is not None:
        print(
            f"Error: Agent files removed but metadata cleanup failed ({lockfile_error}).",
            file=sys.stderr,
        )
        return 1

    uninstall_trace_payload = {
        "schema_version": "1.0",
        "event": "uninstall",
        "agent": normalized_name,
        "removed_path": str(target_dir),
        "removed_from_lockfile": removed_from_lockfile,
        "timestamp": _utc_now_iso(),
    }
    trace_path = write_uninstall_trace(install_root=install_root, payload=uninstall_trace_payload)
    if trace_path is not None:
        print(f"[kinnoo uninstall] Wrote uninstall trace: '{trace_path}'")

    print(f"[kinnoo uninstall] Removed installed agent '{normalized_name}'.")
    return 0
