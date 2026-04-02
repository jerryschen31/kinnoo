"""OpenClaw CLI preflight checks used by kinnoo wrappers.

Feature76 introduces a single reusable preflight helper so command handlers can
consistently enforce OpenClaw CLI availability and minimum version contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import shutil
import subprocess


_VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)")


@dataclass(frozen=True)
class OpenClawPreflightResult:
    ok: bool
    category: str
    message: str
    version: str | None = None


def parse_openclaw_version(raw: str) -> tuple[int, int, int] | None:
    """Parse OpenClaw date-style version output.

    Supports output containing forms like:
    - "2026.3.31"
    - "openclaw 2026.3.31"
    - "v2026.3.31-beta.1"
    """
    match = _VERSION_PATTERN.search(raw or "")
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def _compare_versions(left: tuple[int, int, int], right: tuple[int, int, int]) -> int:
    if left == right:
        return 0
    return 1 if left > right else -1


def _version_to_label(version: tuple[int, int, int]) -> str:
    return f"{version[0]}.{version[1]}.{version[2]}"


def ensure_openclaw_cli(minimum_version: str = "2026.3.28") -> OpenClawPreflightResult:
    """Validate OpenClaw CLI presence and minimum version."""
    required = parse_openclaw_version(minimum_version)
    if required is None:
        return OpenClawPreflightResult(
            ok=False,
            category="openclaw_cli_minimum_constraint_invalid",
            message=(
                "openclaw preflight failed: minimum version constraint is invalid "
                f"('{minimum_version}')."
            ),
        )

    openclaw_path = shutil.which("openclaw")
    if openclaw_path is None:
        return OpenClawPreflightResult(
            ok=False,
            category="openclaw_cli_missing",
            message=(
                "openclaw preflight failed: OpenClaw CLI not found in PATH. "
                "Install OpenClaw CLI and retry."
            ),
        )

    try:
        result = subprocess.run(
            [openclaw_path, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return OpenClawPreflightResult(
            ok=False,
            category="openclaw_cli_version_probe_failed",
            message=f"openclaw preflight failed: unable to execute openclaw --version: {error}",
        )

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        suffix = f" ({detail})" if detail else ""
        return OpenClawPreflightResult(
            ok=False,
            category="openclaw_cli_version_probe_failed",
            message=(
                "openclaw preflight failed: openclaw --version returned non-zero "
                f"exit code{suffix}"
            ),
        )

    parsed = parse_openclaw_version(result.stdout or "")
    if parsed is None:
        return OpenClawPreflightResult(
            ok=False,
            category="openclaw_cli_version_parse_failed",
            message=(
                "openclaw preflight failed: unable to parse OpenClaw CLI version from "
                f"output '{(result.stdout or '').strip()}'"
            ),
        )

    if _compare_versions(parsed, required) < 0:
        return OpenClawPreflightResult(
            ok=False,
            category="openclaw_cli_version_unsupported",
            message=(
                "openclaw preflight failed: OpenClaw CLI version "
                f"{_version_to_label(parsed)} is below required >= {minimum_version}. "
                "Upgrade OpenClaw CLI and retry."
            ),
            version=_version_to_label(parsed),
        )

    return OpenClawPreflightResult(
        ok=True,
        category="openclaw_cli_precheck_ok",
        message=(
            "openclaw preflight passed: OpenClaw CLI version "
            f"{_version_to_label(parsed)} satisfies >= {minimum_version}"
        ),
        version=_version_to_label(parsed),
    )
