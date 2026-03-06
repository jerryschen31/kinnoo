from pathlib import Path
import os
import subprocess

from kinnoo.archive import ArchiveBackend, LocalArchiveBackend


def test_pack_uses_canonical_archive_path_and_storage_abstraction(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-root"
    archive_backend = LocalArchiveBackend(root=archive_root)
    assert isinstance(archive_backend, ArchiveBackend)

    agent_dir = tmp_path / "demo-agent-src"
    agent_dir.mkdir()
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: demo-agent
version: 1.2.3
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

    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    result = subprocess.run(
        ["python3", str(cli_script), "pack", str(agent_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0

    expected_archive_path = archive_backend.archive_path_for(name="demo-agent", version="1.2.3")
    assert expected_archive_path.exists()
    assert f"[kinnoo pack] Archive created: {expected_archive_path}" in output
    assert "[kinnoo pack] Agent version: 1.2.3" in output

    pack_command_source = (Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "pack_command.py").read_text(
        encoding="utf-8"
    )
    assert "LocalArchiveBackend" in pack_command_source
