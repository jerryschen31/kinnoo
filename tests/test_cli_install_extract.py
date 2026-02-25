import subprocess
import sys
import tempfile
import shutil
import os
from pathlib import Path
import zipfile
import pytest

def make_kno_archive(tmp_path, agent_name="testagent"):
    """Helper to create a minimal .kno archive for testing extraction."""
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    # Write a fully valid kinnoo.yaml manifest
    manifest = (
        "name: test-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )
    (agent_dir / "kinnoo.yaml").write_text(manifest)
    (agent_dir / "run.py").write_text("print('hello')\n")
    archive_path = tmp_path / f"{agent_name}.kno"
    with zipfile.ZipFile(archive_path, "w") as z:
        for file in agent_dir.iterdir():
            z.write(file, arcname=file.name)
    return archive_path, agent_dir

def test_install_extracts_archive(tmp_path):
    # Arrange: create .kno archive
    archive_path, agent_dir = make_kno_archive(tmp_path)
    # Remove the original agent_dir to simulate fresh install
    shutil.rmtree(agent_dir)
    assert not agent_dir.exists()
    # Act: run kinnoo install <archive>
    cli_path = os.path.abspath("src/kinnoo/cli.py")
    result = subprocess.run([
        sys.executable, cli_path, "install", str(archive_path)
    ], capture_output=True, text=True)
    # Assert: agent_dir is created and files extracted
    assert result.returncode == 0
    assert agent_dir.exists()
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "run.py").exists()
    assert f"Extracted '{archive_path.name}' to '{agent_dir}'" in result.stdout
