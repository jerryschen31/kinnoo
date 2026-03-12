import os
import re
import subprocess
import sys
from pathlib import Path


def _create_agent_for_pack(agent_dir: Path, *, name: str, version: str, with_blob: bool) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)

    files_block = "\nfiles:\n  - blob.bin" if with_blob else ""
    (agent_dir / "kinnoo.yaml").write_text(
        (
            f"name: {name}\n"
            f"version: {version}\n"
            "entrypoint: run.py\n"
            "runtime:\n"
            "  language: python\n"
            "  version: '>=3.10'\n"
            "  type: one-shot\n"
            "dependencies: []\n"
            f"{files_block}\n"
            "inputs:\n"
            "  type: text\n"
            "outputs:\n"
            "  type: text\n"
        ),
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('pack-size')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    if with_blob:
        # Random bytes are intentionally incompressible so archive size stays above warning threshold.
        (agent_dir / "blob.bin").write_bytes(os.urandom(1200 * 1024))


def test_pack_prints_human_readable_archive_size(tmp_path: Path) -> None:
    agent_dir = tmp_path / "size-line-agent"
    _create_agent_for_pack(agent_dir, name="size-line-agent", version="1.0.0", with_blob=False)

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
    assert re.search(r"\[kinnoo pack\] Archive size: \d+(?:\.\d)? (?:B|KB|MB|GB)", output)


def test_pack_warns_when_archive_exceeds_threshold_override(tmp_path: Path) -> None:
    agent_dir = tmp_path / "size-warning-agent"
    _create_agent_for_pack(agent_dir, name="size-warning-agent", version="1.0.0", with_blob=True)

    archive_root = tmp_path / "archive-root"
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)
    env["KINNOO_PACK_WARN_THRESHOLD_MB"] = "1"

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
    assert "[kinnoo pack] Archive size:" in output
    assert re.search(
        r"Warning: archive is large \([0-9]+\.[0-9] MB\)\. Consider whether all dependencies are necessary\.",
        output,
    )
