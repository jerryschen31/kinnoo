"""OpenClaw logs passthrough wrapper for kinnoo logs command."""

from __future__ import annotations

import subprocess
import sys


def logs_openclaw(*, follow: bool = False, json_output: bool = False) -> int:
    """Delegate to `openclaw logs` with deterministic passthrough flags."""
    command = ["openclaw", "logs"]
    if follow:
        command.append("--follow")
    if json_output:
        command.append("--json")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        print(
            f"Error: OpenClaw logs invocation failed (category=openclaw_logs_invocation_failed): {error}",
            file=sys.stderr,
        )
        return 1

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    return int(result.returncode)
