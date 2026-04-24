from __future__ import annotations

from pathlib import Path
import subprocess


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


