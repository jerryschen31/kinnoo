import subprocess
import sys
import pytest

def test_cli_installable_and_runnable():
    # This test checks that the CLI is installable and runnable via pyproject.toml
    result = subprocess.run([sys.executable, "-m", "kinnoo.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "init" in result.stdout


import tempfile
import shutil
import os
import sys
import venv
from pathlib import Path

def test_run_installs_requirements(tmp_path):
        """Test that kinnoo run installs requirements.txt packages into .venv/"""
        # 1. Create agent dir with requirements.txt specifying a package (e.g., requests)
        agent_dir = tmp_path / "test-agent"
        agent_dir.mkdir()
        (agent_dir / "requirements.txt").write_text("requests==2.31.0\n")
        (agent_dir / "kinnoo.yaml").write_text("""
name: test-agent
version: 0.1.0
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
""")
        (agent_dir / "run.py").write_text("""
import sys\nprint('Hello from run.py')\n""")
        (agent_dir / "README.md").write_text("Test agent.")
        (agent_dir / "tools").mkdir()
        (agent_dir / "prompts").mkdir()

        # 2. Run kinnoo run on that directory
        result = subprocess.run([sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "test input"], capture_output=True, text=True)
        assert result.returncode == 0, f"kinnoo run failed: {result.stderr}"

        # 3. Verify requests is importable in the venv
        venv_python = agent_dir / ".venv" / "bin" / "python"
        if not venv_python.exists():
                venv_python = agent_dir / ".venv" / "Scripts" / "python.exe"  # Windows fallback
        assert venv_python.exists(), ".venv python not found"
        check_code = "import requests; print(requests.__version__)"
        check = subprocess.run([str(venv_python), "-c", check_code], capture_output=True, text=True)
        assert check.returncode == 0, f"requests not importable: {check.stderr}"
        assert check.stdout.strip() == "2.31.0"


def test_run_entrypoint_with_input(tmp_path):
    """Test kinnoo run executes entrypoint with user input as sys.argv[1]"""
    agent_dir = tmp_path / "test-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: test-agent
version: 0.1.0
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
"""
    )
    # run.py prints sys.argv[1] (the input string)
    (agent_dir / "run.py").write_text(
        "import sys\nprint(f'input: {sys.argv[1] if len(sys.argv) > 1 else \"\"}')\n"
    )
    (agent_dir / "README.md").write_text("Test agent.")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    # Run kinnoo run with input string
    input_str = "hello-world"
    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), input_str],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"kinnoo run failed: {result.stderr}"
    assert f"input: {input_str}" in result.stdout or f"input: {input_str}" in result.stderr


def test_run_streams_stdout_stderr(tmp_path, capsys):
    """Test kinnoo run streams both stdout and stderr from entrypoint in real-time."""
    agent_dir = tmp_path / "test-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: test-agent
version: 0.1.0
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
"""
    )
    # run.py prints to both stdout and stderr
    (agent_dir / "run.py").write_text(
        "import sys\nimport time\nprint('stdout: hello', flush=True)\nprint('stderr: error', file=sys.stderr, flush=True)\n"
    )
    (agent_dir / "README.md").write_text("Test agent.")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    # Run kinnoo run and capture output
    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "test input"],
        capture_output=True, text=True
    )
    # Both outputs should appear in either stdout or stderr
    assert "stdout: hello" in result.stdout or "stdout: hello" in result.stderr
    assert "stderr: error" in result.stdout or "stderr: error" in result.stderr
    assert result.returncode == 0


def test_run_exit_code(tmp_path):
    """Test kinnoo run returns entrypoint exit code; non-zero codes propagate."""
    agent_dir = tmp_path / "test-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: test-agent
version: 0.1.0
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
"""
    )
    # run.py exits with code 42
    (agent_dir / "run.py").write_text(
        "import sys\nsys.exit(42)\n"
    )
    (agent_dir / "README.md").write_text("Test agent.")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    # Run kinnoo run and check exit code
    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "test input"],
        capture_output=True, text=True
    )
    assert result.returncode == 42, f"Expected exit code 42, got {result.returncode}"


def test_run_missing_args():
    """Test kinnoo run with missing args prints usage error and exits non-zero."""
    result = subprocess.run([
        sys.executable, "-m", "kinnoo.cli", "run"],
        capture_output=True, text=True
    )
    assert result.returncode != 0, "Expected non-zero exit code for missing args"
    assert "Usage: kinnoo run" in result.stderr
    assert "<agent-dir> '<input>'" in result.stderr


def test_run_missing_entrypoint(tmp_path):
    """Test kinnoo run with missing entrypoint file prints error and aborts."""
    agent_dir = tmp_path / "test-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: test-agent
version: 0.1.0
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
"""
    )
    (agent_dir / "README.md").write_text("Test agent.")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    # Do NOT create run.py

    # Run kinnoo run and check for error
    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "hello!"],
        capture_output=True, text=True
    )
    assert result.returncode != 0, "Expected non-zero exit code for missing entrypoint"
    assert "Entrypoint file" in result.stderr
    assert "not found" in result.stderr


def test_run_corrupted_manifest(tmp_path):
    """Test kinnoo run handles corrupted kinnoo.yaml gracefully (test24)."""
    agent_dir = tmp_path / "test-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    # Write corrupted kinnoo.yaml
    (agent_dir / "kinnoo.yaml").write_text("""
name: test-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
  this is: not valid yaml
inputs:
    type: text
outputs:
    type: text
""")
    (agent_dir / "run.py").write_text("import sys\nprint('Should not run')\n")
    (agent_dir / "README.md").write_text("Test agent.")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    # Run kinnoo run and check for YAML error
    result = subprocess.run([
        sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "hello!"],
        capture_output=True, text=True
    )
    assert result.returncode != 0, "Expected non-zero exit code for corrupted kinnoo.yaml"
    assert "kinnoo.yaml is corrupted" in result.stderr or "invalid YAML" in result.stderr
    assert "Should not run" not in result.stdout


def test_run_permission_error(tmp_path):
    """Test kinnoo run handles permission errors with clear messages (test25)."""
    import stat
    agent_dir = tmp_path / "test-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text("""
name: test-agent
version: 0.1.0
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
""")
    (agent_dir / "run.py").write_text("import sys\nprint('Should not run')\n")
    (agent_dir / "README.md").write_text("Test agent.")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    # Make agent_dir read-only to trigger PermissionError on venv creation
    agent_dir.chmod(stat.S_IREAD)
    try:
        result = subprocess.run([
            sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "hello!"],
            capture_output=True, text=True
        )
        assert result.returncode != 0, "Expected non-zero exit code for permission error"
        assert "Permission denied" in result.stderr
        assert "Should not run" not in result.stdout
    finally:
        # Restore permissions so tmp_path can clean up
        agent_dir.chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
