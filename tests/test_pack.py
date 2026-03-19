import os
import subprocess
import tempfile
import zipfile
import pytest
from pathlib import Path  # <-- Add this import
import shutil

from src.kinnoo.validator import validate

KINNOO_CLI = ["python3", "-m", "src.kinnoo.cli"]


def _pack_env(tmp_path: Path) -> dict[str, str]:
  env = os.environ.copy()
  project_root = str(Path(__file__).parent.parent)
  env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
  env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")
  return env


def _canonical_archive_path(tmp_path: Path, name: str, version: str) -> Path:
  return tmp_path / "archive-root" / name / version / f"{name}.kno"

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
    env = _pack_env(tmp_path)

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
    archive = _canonical_archive_path(tmp_path, "wheelagent", "1.0.0")
    assert archive.exists(), "No .kno archive produced"

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

    env = _pack_env(tmp_path)

    result = subprocess.run(
        KINNOO_CLI + ["pack", str(d)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env
    )
    assert result.returncode == 0, f"kinnoo pack failed: {result.stderr}"

    archive = _canonical_archive_path(tmp_path, "archiveagent", "1.0.0")
    assert archive.exists(), "No .kno archive produced"

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

    env = _pack_env(tmp_path)

    # Run kinnoo pack
    result = subprocess.run(
      KINNOO_CLI + ["pack", str(d)],
      cwd=tmp_path,
      capture_output=True,
      text=True,
      env=env
    )
    assert result.returncode == 0, f"kinnoo pack failed: {result.stderr}"

    archive = _canonical_archive_path(tmp_path, "extractagent", "1.0.0")
    assert archive.exists(), "No .kno archive produced"

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
    archive_root = agent_dir.parent / "archive-root"
    archive_name = f"{agent_dir.name}.kno"
    archive_path = archive_root / agent_dir.name / "1.0.0" / archive_name
    archive_path.parent.mkdir(parents=True, exist_ok=True)
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
        env={**os.environ, "KINNOO_ARCHIVE_ROOT": str(archive_root)},
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
        env={**os.environ, "KINNOO_ARCHIVE_ROOT": str(archive_root)},
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


def test_feature22_pack_includes_assets_recursively_when_enabled(tmp_path):
    agent = tmp_path / "asset-agent"
    agent.mkdir()

    (agent / "assets" / "nested").mkdir(parents=True)
    (agent / "assets" / "nested" / "a.txt").write_text("A\n", encoding="utf-8")
    (agent / "data").mkdir()
    (agent / "data" / "config.json").write_text('{"ok": true}\n', encoding="utf-8")

    (agent / "kinnoo.yaml").write_text(
        """
name: asset-agent
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
assets:
  paths:
    - assets
    - data/config.json
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent / "requirements.txt").write_text("", encoding="utf-8")

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"pack failed: {result.stderr}"

    archive = _canonical_archive_path(tmp_path, "asset-agent", "1.0.0")
    assert archive.exists()

    with zipfile.ZipFile(archive, "r") as zf:
        names = set(zf.namelist())
        assert "assets/nested/a.txt" in names
        assert "data/config.json" in names


def test_feature22_pack_skips_assets_when_bundle_false(tmp_path):
    agent = tmp_path / "asset-optout"
    agent.mkdir()
    (agent / "assets").mkdir()
    (agent / "assets" / "secret.txt").write_text("no bundle\n", encoding="utf-8")

    (agent / "kinnoo.yaml").write_text(
        """
name: asset-optout
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
assets:
  bundle: false
  paths:
    - assets
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent / "requirements.txt").write_text("", encoding="utf-8")

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "Asset bundling disabled" in output

    archive = _canonical_archive_path(tmp_path, "asset-optout", "1.0.0")
    assert archive.exists()

    with zipfile.ZipFile(archive, "r") as zf:
        names = set(zf.namelist())
        assert "assets/secret.txt" not in names


def test_feature22_pack_rejects_asset_path_traversal(tmp_path):
    workspace_secret = tmp_path / "secret.txt"
    workspace_secret.write_text("hidden\n", encoding="utf-8")

    agent = tmp_path / "asset-traversal"
    agent.mkdir()
    (agent / "kinnoo.yaml").write_text(
        """
name: asset-traversal
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
assets:
  paths:
    - ../secret.txt
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent / "requirements.txt").write_text("", encoding="utf-8")

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "escapes agent directory" in output


def test_feature22_pack_warns_on_missing_asset_path(tmp_path):
    agent = tmp_path / "asset-missing"
    agent.mkdir()
    (agent / "assets").mkdir()
    (agent / "assets" / "present.txt").write_text("present\n", encoding="utf-8")

    (agent / "kinnoo.yaml").write_text(
        """
name: asset-missing
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
assets:
  paths:
    - assets/present.txt
    - assets/missing.txt
""".strip()
        + "\n",
        encoding="utf-8",
    )

    (agent / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent / "requirements.txt").write_text("", encoding="utf-8")

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "Declared asset path 'assets/missing.txt' was not found" in output

    archive = _canonical_archive_path(tmp_path, "asset-missing", "1.0.0")
    assert archive.exists()
    with zipfile.ZipFile(archive, "r") as zf:
        names = set(zf.namelist())
        assert "assets/present.txt" in names
        assert "assets/missing.txt" not in names


def test_feature35_pack_state_snapshot_layout(tmp_path):
    """Feature35 test293: pack captures state_dirs snapshots with deterministic layout."""
    agent = tmp_path / "feature35-state-pack"
    agent.mkdir()

    (agent / "memory" / "session").mkdir(parents=True)
    (agent / "memory" / "session" / "journal.md").write_text("state journal\n", encoding="utf-8")
    (agent / "state" / "cache").mkdir(parents=True)
    (agent / "state" / "cache" / "index.json").write_text('{"warm": true}\n', encoding="utf-8")

    (agent / "assets").mkdir()
    (agent / "assets" / "guide.txt").write_text("immutable docs\n", encoding="utf-8")

    (agent / "kinnoo.yaml").write_text(
        """
name: feature35-state-pack
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
assets:
  paths:
    - assets
state_dirs:
  - memory
  - path: state/cache
    exclude:
      - '*.log'
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent / "run.py").write_text("print('feature35')\n", encoding="utf-8")
    (agent / "requirements.txt").write_text("", encoding="utf-8")

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"pack failed: {result.stderr}"

    archive = _canonical_archive_path(tmp_path, "feature35-state-pack", "1.0.0")
    assert archive.exists(), "Expected .kno archive to be created"

    with zipfile.ZipFile(archive, "r") as zf:
        names = sorted(zf.namelist())
        assert "assets/guide.txt" in names
        assert "state_snapshots/memory/session/journal.md" in names
        assert "state_snapshots/state/cache/index.json" in names
        assert all(not name.startswith("memory/") for name in names)
        assert all(not name.startswith("state/cache/") for name in names)


def test_feature22_pack_size_warning_uses_assets_threshold(tmp_path):
    default_agent = tmp_path / "asset-threshold-default"
    default_agent.mkdir()
    (default_agent / "kinnoo.yaml").write_text(
        """
name: asset-threshold-default
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
assets:
  paths: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (default_agent / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (default_agent / "requirements.txt").write_text("", encoding="utf-8")

    default_env = _pack_env(tmp_path)
    default_env.pop("KINNOO_PACK_WARN_THRESHOLD_MB", None)
    default_result = subprocess.run(
        KINNOO_CLI + ["pack", str(default_agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=default_env,
    )
    default_output = f"{default_result.stdout}\n{default_result.stderr}"
    assert default_result.returncode == 0
    assert "Warning: archive is large" not in default_output

    override_agent = tmp_path / "asset-threshold-override"
    override_agent.mkdir()
    (override_agent / "assets").mkdir()
    (override_agent / "assets" / "tiny.txt").write_text("tiny\n", encoding="utf-8")
    (override_agent / "kinnoo.yaml").write_text(
        """
name: asset-threshold-override
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
assets:
  max_bundle_size_mb: 0.000001
  paths:
    - assets
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (override_agent / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (override_agent / "requirements.txt").write_text("", encoding="utf-8")

    override_env = _pack_env(tmp_path)
    override_env.pop("KINNOO_PACK_WARN_THRESHOLD_MB", None)
    override_result = subprocess.run(
        KINNOO_CLI + ["pack", str(override_agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=override_env,
    )
    override_output = f"{override_result.stdout}\n{override_result.stderr}"
    assert override_result.returncode == 0
    assert "Warning: archive is large" in override_output


def test_feature22_pack_warns_on_secret_like_asset_filenames(tmp_path):
    agent = tmp_path / "asset-secret-filenames"
    agent.mkdir()
    (agent / "secrets").mkdir(parents=True)
    (agent / "secrets" / ".env").write_text("DUMMY=1\n", encoding="utf-8")
    (agent / "secrets" / "id_rsa").write_text("not-real-key\n", encoding="utf-8")
    (agent / "secrets" / "tls.key").write_text("not-real-tls-key\n", encoding="utf-8")
    (agent / "secrets" / "certificate.p12").write_text("not-real-p12\n", encoding="utf-8")
    (agent / "secrets" / "cert-store.pfx").write_text("not-real-pfx\n", encoding="utf-8")
    (agent / "secrets" / "credentials.json").write_text("{}\n", encoding="utf-8")

    (agent / "kinnoo.yaml").write_text(
        """
name: asset-secret-filenames
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
assets:
  paths:
    - secrets
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent / "requirements.txt").write_text("", encoding="utf-8")

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "Asset security sweep warnings:" in output
    assert "secrets/.env: secret-like filename (.env)" in output
    assert "secrets/id_rsa: secret-like filename (id_rsa)" in output
    assert "secrets/tls.key: secret-like filename (.key)" in output
    assert "secrets/certificate.p12: secret-like filename (*.p12)" in output
    assert "secrets/cert-store.pfx: secret-like filename (*.pfx)" in output
    assert "secrets/credentials.json: secret-like filename (credential marker)" in output


def test_feature22_pack_text_secret_scan_warning_only_with_binary_skip(tmp_path):
    agent = tmp_path / "asset-text-and-binary-scan"
    agent.mkdir()
    (agent / "assets").mkdir(parents=True)
    (agent / "assets" / "token.txt").write_text(
        "api_key = sk_test_token_123456789\n",
        encoding="utf-8",
    )
    (agent / "assets" / "blob.bin").write_bytes(b"\x00\x01\x02\x03")

    (agent / "kinnoo.yaml").write_text(
        """
name: asset-text-and-binary-scan
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
assets:
  paths:
    - assets
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent / "requirements.txt").write_text("", encoding="utf-8")

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "Asset security sweep warnings:" in output
    assert "assets/token.txt: credential-like text pattern (API key assignment)" in output
    assert "assets/blob.bin: skipped binary file for text credential scan" in output
    assert "heuristic credential scan over assets - warning-only" in output


def test_feature26_filesystem_mcp_fixture_valid_and_packable(tmp_path: Path) -> None:
    """Feature26 test236: filesystem mcp-server fixture validates and packs."""
    source_fixture = Path(__file__).resolve().parents[1] / "scratch" / "feature26-filesystem-mcp-server"
    fixture_dir = tmp_path / "feature26-filesystem-mcp-server"
    shutil.copytree(source_fixture, fixture_dir)

    manifest_path = fixture_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid is True, f"Expected filesystem mcp fixture manifest to validate; errors: {errors}"
    assert errors == []

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(fixture_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"kinnoo pack failed for filesystem mcp fixture: {result.stderr}"

    archive = _canonical_archive_path(tmp_path, "filesystem-mcp-server", "1.0.0")
    assert archive.exists(), "Expected .kno archive for filesystem mcp fixture"

    with zipfile.ZipFile(archive, "r") as zf:
        names = set(zf.namelist())
        assert "kinnoo.yaml" in names
        assert "run.py" in names
        assert "requirements.txt" in names


def test_feature26_github_mcp_fixture_valid_and_packable(tmp_path: Path) -> None:
    """Feature26 test239: github mcp-server fixture validates and packs."""
    source_fixture = Path(__file__).resolve().parents[1] / "scratch" / "feature26-github-mcp-server"
    fixture_dir = tmp_path / "feature26-github-mcp-server"
    shutil.copytree(source_fixture, fixture_dir)

    manifest_path = fixture_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid is True, f"Expected github mcp fixture manifest to validate; errors: {errors}"
    assert errors == []

    env = _pack_env(tmp_path)
    result = subprocess.run(
        KINNOO_CLI + ["pack", str(fixture_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"kinnoo pack failed for github mcp fixture: {result.stderr}"

    archive = _canonical_archive_path(tmp_path, "github-mcp-server", "1.0.0")
    assert archive.exists(), "Expected .kno archive for github mcp fixture"

    with zipfile.ZipFile(archive, "r") as zf:
        names = set(zf.namelist())
        assert "kinnoo.yaml" in names
        assert "run.py" in names
        assert "requirements.txt" in names


def test_feature31_pack_node_modules_excluded_lockfiles_preserved(monkeypatch, tmp_path: Path) -> None:
    from kinnoo import install_command

    monkeypatch.setattr(
        install_command,
        "check_node_runtime_constraint",
        lambda _constraint: (True, "runtime version check passed: current Node 22.0.0 satisfies runtime.version '>=22'"),
    )
    monkeypatch.setattr(
        install_command,
        "check_node_package_manager_availability",
        lambda _package_manager: (True, "dependency readiness check passed: node package manager is available"),
    )

    agent = tmp_path / "feature31-node-pack"
    agent.mkdir()
    (agent / "node_modules" / "left-pad").mkdir(parents=True)
    (agent / "node_modules" / "left-pad" / "index.js").write_text("module.exports = {};\n", encoding="utf-8")
    (agent / "data").mkdir()
    (agent / "data" / "notes.txt").write_text("keep this asset\n", encoding="utf-8")

    (agent / "kinnoo.yaml").write_text(
        """
name: feature31-node-pack
version: 1.0.0
entrypoint: run.js
runtime:
  language: nodejs
  version: '>=22'
  type: one-shot
dependencies: []
inputs:
  type: string
outputs:
  type: string
assets:
  paths:
    - node_modules
    - data
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent / "run.js").write_text("console.log('node agent');\n", encoding="utf-8")
    (agent / "requirements.txt").write_text("", encoding="utf-8")
    (agent / "package.json").write_text(
      '{"name":"feature31-node-pack","version":"1.0.0","dependencies":{"left-pad":"1.3.0"}}\n',
      encoding="utf-8",
    )
    (agent / "package-lock.json").write_text('{"name":"feature31-node-pack","lockfileVersion":3}\n', encoding="utf-8")
    (agent / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")

    env = _pack_env(tmp_path)
    pack_result = subprocess.run(
        KINNOO_CLI + ["pack", str(agent)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert pack_result.returncode == 0, f"pack failed: {pack_result.stderr}"

    archive = _canonical_archive_path(tmp_path, "feature31-node-pack", "1.0.0")
    assert archive.exists(), "Expected .kno archive for feature31 node pack fixture"

    with zipfile.ZipFile(archive, "r") as zf:
        names = set(zf.namelist())
        assert "package.json" in names
        assert "package-lock.json" in names
        assert "pnpm-lock.yaml" in names
        assert "data/notes.txt" in names
        assert not any(name.startswith("node_modules/") for name in names)

    install_calls: list[tuple[list[str], Path | None]] = []

    class _Completed:
        def __init__(self, returncode: int = 0, stderr_text: str = ""):
            self.returncode = returncode
            self.stderr = stderr_text
            self.stdout = ""

    def _fake_run(command, *args, **kwargs):
        del args
        install_calls.append((list(command), kwargs.get("cwd")))
        executable = Path(command[0]).name
        if executable == "npm":
            return _Completed(0)
        return _Completed(0)

    monkeypatch.setattr(install_command.subprocess, "run", _fake_run)

    install_target = tmp_path / "feature31-node-pack-install"
    install_result = install_command.install_agent(
        archive_path=str(archive),
        target_dir_arg=str(install_target),
        assume_yes=True,
    )
    assert install_result == 0
    assert (["npm", "install"], install_target.resolve()) in [
        (command, cwd.resolve() if isinstance(cwd, Path) else cwd)
        for command, cwd in install_calls
    ]
