import os
import subprocess
import tempfile
import zipfile
import pytest
from pathlib import Path  # <-- Add this import
import shutil

KINNOO_CLI = ["python3", "-m", "src.kinnoo.cli"]

@pytest.fixture
def agent_dir(tmp_path):
    # Create a minimal valid agent directory for testing
    d = tmp_path / "myagent"
    d.mkdir()
    (d / "kinnoo.yaml").write_text("name: myagent\nversion: 1.0.0\nentrypoint: run.py\nruntime:\n  language: python\n  version: '>=3.10'\n  type: one-shot\ndependencies: []\ninputs:\n  type: text\noutputs:\n  type: text\n")
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
version: 1.0.0
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
version: 1.0.0
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
version: 1.0.0
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
version: 1.0.0
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

def test_manual_extraction_verifies_files(tmp_path):
    """
    test50: Manual extraction of .kno archive verifies required files
    Steps:
      1. Extract .kno archive using zipfile (since kinnoo pack uses zip format)
      2. Check agent-dir for requirements.txt, run.py, kinnoo.yaml, and any files listed in manifest
      3. If any are missing, throw error
    """
    d = tmp_path / "extractagent"
    d.mkdir()
    # Minimal valid manifest
    manifest = (
      "name: extractagent\n"
      "version: 1.0.0\n"
      "entrypoint: run.py\n"
      "runtime:\n"
      "  language: python\n"
      "  version: '>=3.10'\n"
      "  type: one-shot\n"
      "dependencies: []\n"
      "inputs:\n"
      "  type: text\n"
      "outputs:\n"
      "  type: text\n"
      "extra_file: extra.txt\n"
    )
    (d / "kinnoo.yaml").write_text(manifest)
    (d / "run.py").write_text("print('extract test')\n")
    (d / "requirements.txt").write_text("wheel\n")
    (d / "extra.txt").write_text("extra file contents\n")

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

    archive = None
    for f in tmp_path.iterdir():
      if f.suffix == ".kno":
        archive = f
        break
    assert archive is not None, "No .kno archive produced"

    # Extract archive to a new directory
    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir()
    with zipfile.ZipFile(archive, "r") as z:
      z.extractall(extract_dir)

    # Check for required files
    required_files = ["kinnoo.yaml", "run.py", "requirements.txt", "extra.txt"]
    for fname in required_files:
      fpath = extract_dir / fname
      assert fpath.exists(), f"Required file {fname} missing after extraction"


def test_pack_prompts_before_overwrite_existing_archive(agent_dir):
    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    cli_cmd = ["python3", str(cli_script)]
    archive_name = f"{agent_dir.name}.kno"
    archive_path = agent_dir.parent / archive_name
    original_bytes = b"DO_NOT_OVERWRITE"
    archive_path.write_bytes(original_bytes)

    prompt = (
        f"({archive_name}) already exists - are you sure you want to overwrite? (y/n): "
    )

    decline_result = subprocess.run(
        cli_cmd + ["pack", str(agent_dir)],
        cwd=agent_dir.parent,
        input="n\n",
        capture_output=True,
        text=True,
    )
    decline_output = f"{decline_result.stdout}\n{decline_result.stderr}"
    assert prompt in decline_output
    assert decline_result.returncode != 0
    assert archive_path.read_bytes() == original_bytes

    confirm_result = subprocess.run(
        cli_cmd + ["pack", str(agent_dir)],
        cwd=agent_dir.parent,
        input="y\n",
        capture_output=True,
        text=True,
    )
    confirm_output = f"{confirm_result.stdout}\n{confirm_result.stderr}"
    assert prompt in confirm_output
    assert confirm_result.returncode == 0
    assert archive_path.read_bytes() != original_bytes

    with zipfile.ZipFile(archive_path, "r") as archive_file:
        assert "kinnoo.yaml" in archive_file.namelist()


def test_pack_bump_flag_and_version_output_line(tmp_path):
    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    cli_cmd = ["python3", str(cli_script)]

    agent_dir = tmp_path / "bump-agent"
    agent_dir.mkdir()
    manifest_path = agent_dir / "kinnoo.yaml"
    manifest_path.write_text(
        """
name: bump-agent
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

    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")

    def run_pack(*extra_args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cli_cmd + ["pack", str(agent_dir), *extra_args],
            cwd=tmp_path,
            input=input_text,
            capture_output=True,
            text=True,
        env=env,
        )

    first = run_pack()
    first_output = f"{first.stdout}\n{first.stderr}"
    assert first.returncode == 0
    assert "[kinnoo pack] Agent version: 1.2.3" in first_output
    assert "version: 1.2.3" in manifest_path.read_text(encoding="utf-8")

    patch = run_pack("--bump", "patch", input_text="y\n")
    patch_output = f"{patch.stdout}\n{patch.stderr}"
    assert patch.returncode == 0
    assert "[kinnoo pack] Agent version: 1.2.4" in patch_output
    assert "version: 1.2.4" in manifest_path.read_text(encoding="utf-8")

    minor = run_pack("--bump", "minor", input_text="y\n")
    minor_output = f"{minor.stdout}\n{minor.stderr}"
    assert minor.returncode == 0
    assert "[kinnoo pack] Agent version: 1.3.0" in minor_output
    assert "version: 1.3.0" in manifest_path.read_text(encoding="utf-8")

    major = run_pack("--bump", "major", input_text="y\n")
    major_output = f"{major.stdout}\n{major.stderr}"
    assert major.returncode == 0
    assert "[kinnoo pack] Agent version: 2.0.0" in major_output
    assert "version: 2.0.0" in manifest_path.read_text(encoding="utf-8")

    invalid = run_pack("--bump", "banana")
    invalid_output = f"{invalid.stdout}\n{invalid.stderr}"
    assert invalid.returncode != 0
    assert "[kinnoo pack] Agent version:" not in invalid_output
