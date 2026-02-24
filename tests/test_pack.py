import os
import subprocess
import tempfile
import zipfile
import pytest
from pathlib import Path  # <-- Add this import

KINNOO_CLI = ["python3", "-m", "src.kinnoo.cli"]

@pytest.fixture
def agent_dir(tmp_path):
    # Create a minimal valid agent directory for testing
    d = tmp_path / "myagent"
    d.mkdir()
    (d / "kinnoo.yaml").write_text("name: myagent\nversion: 0.1.0\nentrypoint: run.py\nruntime:\n  language: python\n  version: '>=3.10'\n  type: one-shot\ndependencies: []\ninputs:\n  type: text\noutputs:\n  type: text\n")
    (d / "run.py").write_text("print('hello')\n")
    (d / "requirements.txt").write_text("")
    return d

def test_pack_missing_argument_prints_usage(tmp_path):
    result = subprocess.run(KINNOO_CLI + ["pack"], cwd=tmp_path, capture_output=True, text=True)
    assert "Usage: kinnoo pack <agent-dir>" in result.stdout or result.stderr
    assert result.returncode != 0

def test_pack_inside_agent_dir_prints_error(agent_dir):
    # Run kinnoo pack . from inside agent dir
    result = subprocess.run(KINNOO_CLI + ["pack", "."], cwd=agent_dir, capture_output=True, text=True)
    assert "Do not run kinnoo pack from inside the agent directory" in result.stdout or result.stderr
    assert result.returncode != 0
    # No .kno archive should be created
    assert not any(f.suffix == ".kno" for f in agent_dir.iterdir())

def test_pack_invalid_manifest_aborts(tmp_path):
    # Create agent dir with invalid kinnoo.yaml (missing required field)
    d = tmp_path / "badagent"
    d.mkdir()
    # Missing 'entrypoint' field
    (d / "kinnoo.yaml").write_text("""
name: badagent
version: 0.1.0
runtime:
  language: python
  version: '>=3.10'
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""")
    (d / "run.py").write_text("print('hello')\n")
    (d / "requirements.txt").write_text("")
    result = subprocess.run(KINNOO_CLI + ["pack", str(d)], cwd=tmp_path, capture_output=True, text=True)
    assert "Manifest validation failed" in result.stdout or result.stderr
    assert "entrypoint" in result.stdout or result.stderr
    assert result.returncode != 0


def test_pack_missing_required_files_aborts(tmp_path):
    # Create agent dir with valid kinnoo.yaml but missing run.py
    d = tmp_path / "missingfile"
    d.mkdir()
    (d / "kinnoo.yaml").write_text("""
name: missingfile
version: 0.1.0
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
""")
    (d / "requirements.txt").write_text("")
    # Do NOT create run.py
    result = subprocess.run(KINNOO_CLI + ["pack", str(d)], cwd=tmp_path, capture_output=True, text=True)
    # This will fail at the next step (task25), so for now just check that pack does not succeed
    assert result.returncode != 0

def test_pack_includes_wheel_files(tmp_path):
    # Create agent dir with requirements.txt listing a simple dependency
    d = tmp_path / "wheelagent"
    d.mkdir()
    (d / "kinnoo.yaml").write_text("""
name: wheelagent
version: 0.1.0
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
""")
    (d / "run.py").write_text("print('hello')\n")
    # Use a tiny, always-available package for test (e.g., 'wheel')
    (d / "requirements.txt").write_text("wheel\n")

    # Set PYTHONPATH to project root so src.kinnoo.cli is importable
    env = os.environ.copy()
    project_root = str(Path(__file__).parent.parent)
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    # Run kinnoo pack
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(d)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env
    )
    assert result.returncode == 0, f"kinnoo pack failed: {result.stderr}"

    # Find the .kno archive
    archive = None
    for f in tmp_path.iterdir():
        if f.suffix == ".kno":
            archive = f
            break
    assert archive is not None, "No .kno archive produced"

    # Inspect archive for wheel files
    with zipfile.ZipFile(archive, "r") as z:
        wheel_files = [name for name in z.namelist() if name.endswith(".whl")]
        assert wheel_files, "No wheel files found in archive"
        # Optionally, check that the wheel for 'wheel' is present
        assert any("wheel" in wf for wf in wheel_files), f"Expected 'wheel' wheel file, found: {wheel_files}"

def test_pack_creates_correct_archive_structure(tmp_path):
    """
    Test that kinnoo pack creates a .kno archive with the correct structure:
    - kinnoo.yaml
    - entrypoint (run.py)
    - requirements.txt
    - wheels/ (with at least one wheel file)
    """
    d = tmp_path / "archiveagent"
    d.mkdir()
    (d / "kinnoo.yaml").write_text("""
name: archiveagent
version: 0.1.0
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
""")
    (d / "run.py").write_text("print('archive test')\n")
    (d / "requirements.txt").write_text("wheel\n")

    env = os.environ.copy()
    project_root = str(Path(__file__).parent.parent)
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        KINNOO_CLI + ["pack", str(d)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env
    )
    assert result.returncode == 0, f"kinnoo pack failed: {result.stderr}"

    archive = None
    for f in tmp_path.iterdir():
        if f.suffix == ".kno":
            archive = f
            break
    assert archive is not None, "No .kno archive produced"

    with zipfile.ZipFile(archive, "r") as z:
        names = set(z.namelist())
        assert "kinnoo.yaml" in names, "kinnoo.yaml missing from archive"
        assert "run.py" in names, "run.py missing from archive"
        assert "requirements.txt" in names, "requirements.txt missing from archive"
        wheel_files = [n for n in names if n.startswith("wheels/") and n.endswith(".whl")]
        assert wheel_files, "No wheel files in wheels/ directory"
