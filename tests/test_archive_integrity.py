import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

from kinnoo.checksum import (
    compute_file_sha256,
    format_checksum_sidecar_line,
    parse_checksum_sidecar_text,
    verify_archive_checksum,
)


def _create_minimal_agent(agent_dir: Path, name: str, version: str) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: {name}
version: {version}
entrypoint: run.py
runtime:
  language: python
  version: '>=3.10'
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")


def _sha256_of(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def test_checksum_helpers_compute_and_parse(tmp_path: Path) -> None:
    archive_path = tmp_path / "fixture.kno"
    archive_path.write_bytes(b"deterministic-archive-bytes")

    computed_digest = compute_file_sha256(archive_path)
    assert computed_digest == _sha256_of(archive_path)

    sidecar_line = format_checksum_sidecar_line(computed_digest, archive_path.name)
    parsed_digest, parsed_filename = parse_checksum_sidecar_text(sidecar_line)
    assert parsed_digest == computed_digest
    assert parsed_filename == archive_path.name

    is_match, actual_digest = verify_archive_checksum(archive_path, parsed_digest)
    assert is_match is True
    assert actual_digest == computed_digest


def test_pack_generates_checksum_sidecar(tmp_path: Path) -> None:
    agent_dir = tmp_path / "checksum-agent-src"
    _create_minimal_agent(agent_dir, name="checksum-agent", version="1.0.0")

    archive_root = tmp_path / "archive-root"
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_script), "pack", str(agent_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output

    archive_path = archive_root / "checksum-agent" / "1.0.0" / "checksum-agent.kno"
    checksum_path = archive_path.with_name(f"{archive_path.name}.sha256")

    assert archive_path.exists(), "Expected packed archive to exist"
    assert checksum_path.exists(), "Expected checksum sidecar to be generated"

    checksum_line = checksum_path.read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"[0-9a-f]{64}\s{2}checksum-agent\.kno", checksum_line)

    expected_digest = _sha256_of(archive_path)
    assert checksum_line == f"{expected_digest}  checksum-agent.kno"
    assert f"[kinnoo pack] Checksum sidecar written: {checksum_path}" in output


def test_pack_stores_checksum_with_local_archive(tmp_path: Path) -> None:
    agent_dir = tmp_path / "local-archive-agent-src"
    _create_minimal_agent(agent_dir, name="local-archive-agent", version="2.3.4")

    archive_root = tmp_path / "custom-local-archive"
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_script), "pack", str(agent_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output

    version_dir = archive_root / "local-archive-agent" / "2.3.4"
    archive_path = version_dir / "local-archive-agent.kno"
    checksum_path = version_dir / "local-archive-agent.kno.sha256"

    assert archive_path.exists(), "Expected archive in canonical local archive destination"
    assert checksum_path.exists(), "Expected checksum sidecar beside archived .kno artifact"

    checksum_line = checksum_path.read_text(encoding="utf-8").strip()
    digest_token, filename_token = checksum_line.split("  ")
    assert digest_token == _sha256_of(archive_path)
    assert filename_token == archive_path.name
    assert f"[kinnoo pack] Archive created: {archive_path}" in output
    assert f"[kinnoo pack] Checksum sidecar written: {checksum_path}" in output
