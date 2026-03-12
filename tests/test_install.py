import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import pytest

def make_dummy_kno_archive(archive_path, files=None):
    import zipfile
    files = files or {
        "kinnoo.yaml": (
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
        ),
        "run.py": "print('hello')\n"
    }
    with zipfile.ZipFile(archive_path, "w") as z:
        for fname, content in files.items():
            z.writestr(fname, content)

@pytest.mark.integration
def test_install_extracts_to_user_specified_directory(tmp_path):
    # Setup: create dummy .kno archive
    archive_path = tmp_path / "test-agent.kno"
    make_dummy_kno_archive(archive_path)
    target_dir = tmp_path / "myagent_dir"

    # Step1: Run kinnoo install <archive.kno> myagent_dir
    result = subprocess.run([
        "python3", "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"Install failed: {result.stderr}"
    assert target_dir.exists(), "Target directory not created"
    assert (target_dir / "kinnoo.yaml").exists(), "kinnoo.yaml missing"
    assert (target_dir / "run.py").exists(), "run.py missing"

    # Step2: Run kinnoo install <archive.kno> myagent_dir when directory exists (without --force)
    result2 = subprocess.run([
        "python3", "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"
    ], capture_output=True, text=True)
    assert result2.returncode != 0, "Should fail if directory exists and --force not used"
    assert "already exists" in result2.stderr, "Error message missing for existing directory"

    # Step3: --force is paused; skip this step
