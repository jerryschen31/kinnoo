from __future__ import annotations

import re
from pathlib import Path


EXPOSURE_PATTERNS: list[tuple[str, str]] = [
    (r"print\s*\(.*os\.environ", "print() with os.environ access"),
    (r"print\s*\(.*os\.getenv", "print() with os.getenv() access"),
    (r"log\w*\.\w+\(.*os\.environ", "logging with os.environ access"),
    (r"log\w*\.\w+\(.*os\.getenv", "logging with os.getenv() access"),
    (r"\.write\s*\(.*os\.environ", "file write with os.environ access"),
    (r"\.write\s*\(.*os\.getenv", "file write with os.getenv() access"),
]


def sweep_env_var_exposure(agent_dir: Path, declared_env_vars: list[str]) -> list[str]:
    """Heuristically scan for potential env-var exposure patterns in Python source files.

    Returns warnings formatted as "<file>:<line>: <description>".
    """
    del declared_env_vars

    warnings: list[str] = []
    if not agent_dir.exists() or not agent_dir.is_dir():
        return warnings

    compiled_patterns = [
        (re.compile(pattern, re.IGNORECASE), description)
        for pattern, description in EXPOSURE_PATTERNS
    ]

    for python_file in sorted(agent_dir.rglob("*.py")):
        if ".venv" in python_file.parts:
            continue

        try:
            lines = python_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue

        relative_path = python_file.relative_to(agent_dir)
        for line_number, line_text in enumerate(lines, start=1):
            for compiled_pattern, description in compiled_patterns:
                if compiled_pattern.search(line_text):
                    warnings.append(f"{relative_path}:{line_number}: {description}")
                    break

    return warnings
