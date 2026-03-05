import os
import subprocess
import sys
import zipfile
from pathlib import Path


def test_publish_cli_usage_and_local_flag(tmp_path: Path) -> None:
    usage_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish"],
        capture_output=True,
        text=True,
    )

    assert usage_result.returncode != 0
    assert "Usage: kinnoo publish <archive.kno> [--local]" in usage_result.stderr

    archive_path = tmp_path / "demo-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "kinnoo.yaml",
            """
name: demo-agent
version: 1.2.3
entrypoint: run.py
runtime:
  language: python
  version: ">=3.10"
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""",
        )
        archive_zip.writestr("run.py", "print('hello')\n")

    registry_root = tmp_path / "registry-sandbox"
    env = dict(**os.environ, KINNOO_REGISTRY_ROOT=str(registry_root))

    publish_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish", str(archive_path), "--local"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert publish_result.returncode == 0
    assert "Published demo-agent==1.2.3" in publish_result.stdout

    expected_archive = (
        registry_root / "demo-agent" / "1.2.3" / "demo-agent.kno"
    )
    assert expected_archive.exists()
