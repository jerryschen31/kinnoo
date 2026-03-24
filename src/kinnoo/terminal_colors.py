from __future__ import annotations

import os
import sys
from typing import TextIO

_RESET = "\033[0m"
_COLOR_CODES = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    # These shades intentionally mirror argparse's default help palette seen in
    # `kinnoo inspect -h` so top-level help appears consistent.
    "purple": "\033[34m",
    "pink": "\033[35m",
    "light_blue": "\033[36m",
    "neon_green": "\033[32m",
}
_BOLD = "\033[1m"


def _env_truthy(name: str) -> bool:
    value = os.getenv(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def color_enabled(stream: TextIO | None = None) -> bool:
    if os.getenv("NO_COLOR") is not None:
        return False
    if os.getenv("TERM", "").strip().lower() == "dumb":
        return False
    if _env_truthy("KINNOO_FORCE_COLOR"):
        return True

    active_stream = stream or sys.stdout
    if not hasattr(active_stream, "isatty"):
        return False
    return bool(active_stream.isatty())


def style_text(text: str, *, color: str | None = None, bold: bool = False, stream: TextIO | None = None) -> str:
    if not color_enabled(stream=stream):
        return text

    segments: list[str] = []
    if bold:
        segments.append(_BOLD)
    if color in _COLOR_CODES:
        segments.append(_COLOR_CODES[color])

    if not segments:
        return text
    return "".join(segments) + text + _RESET


def status_color(status: str) -> str:
    normalized = status.strip().upper()
    if normalized == "PASS":
        return "green"
    if normalized == "FAIL":
        return "red"
    if normalized == "WARN":
        return "yellow"
    return "cyan"
