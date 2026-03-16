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

ASSET_FILENAME_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\.env($|\.)", re.IGNORECASE), "secret-like filename (.env)"),
    (re.compile(r"\.pem$", re.IGNORECASE), "secret-like filename (.pem)"),
    (re.compile(r"^id_rsa(\.pub)?$", re.IGNORECASE), "secret-like filename (id_rsa)"),
    (re.compile(r"credentials?", re.IGNORECASE), "secret-like filename (credential marker)"),
]

ASSET_TEXT_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"AKIA[0-9A-Z]{16}"),
        "credential-like text pattern (AWS access key)",
    ),
    (
        re.compile(r"aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{16,}", re.IGNORECASE),
        "credential-like text pattern (AWS secret key assignment)",
    ),
    (
        re.compile(r"api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}", re.IGNORECASE),
        "credential-like text pattern (API key assignment)",
    ),
    (
        re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|PRIVATE) KEY-----"),
        "credential-like text pattern (private key block)",
    ),
]

DEFAULT_ASSET_TEXT_SCAN_MAX_BYTES = 128 * 1024


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


def _looks_binary(content: bytes) -> bool:
    return b"\x00" in content


def sweep_asset_credential_risks(
    agent_dir: Path,
    asset_file_paths: list[Path],
    max_text_scan_bytes: int = DEFAULT_ASSET_TEXT_SCAN_MAX_BYTES,
) -> list[str]:
    """Heuristically scan bundled asset files for credential-like risks.

    Returns warning strings. Scan is warning-only and never blocking.
    """
    warnings: list[str] = []

    for asset_file in sorted(asset_file_paths):
        if not asset_file.exists() or not asset_file.is_file():
            continue

        try:
            relative_path = asset_file.relative_to(agent_dir).as_posix()
        except ValueError:
            # Defensive fallback; caller should already pass in-agent files.
            relative_path = asset_file.name

        basename = asset_file.name
        for pattern, description in ASSET_FILENAME_PATTERNS:
            if pattern.search(basename):
                warnings.append(f"{relative_path}: {description}")

        try:
            raw_content = asset_file.read_bytes()
        except OSError:
            continue

        if _looks_binary(raw_content):
            warnings.append(
                f"{relative_path}: skipped binary file for text credential scan"
            )
            continue

        text_window = raw_content[:max_text_scan_bytes]
        try:
            text_content = text_window.decode("utf-8")
        except UnicodeDecodeError:
            warnings.append(
                f"{relative_path}: skipped binary file for text credential scan"
            )
            continue

        for pattern, description in ASSET_TEXT_SECRET_PATTERNS:
            if pattern.search(text_content):
                warnings.append(f"{relative_path}: {description}")

    return warnings
