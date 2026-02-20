import subprocess
import sys
import re
import os
import pytest
from pathlib import Path

KINNOO_CLI = [sys.executable, "-m", "kinnoo.cli"]


def run_cli(args, cwd=None):
    """Run kinnoo CLI with args, return (exit_code, stdout, stderr)"""
    proc = subprocess.Popen(
        [sys.executable, "-m", "kinnoo.cli"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        text=True,
    )
    out, err = proc.communicate()
    return proc.returncode, out, err


def test_init_missing_name_prints_usage(tmp_path):
    code, out, err = run_cli(["init"], cwd=tmp_path)
    assert code != 0
    assert "Usage" in err
    assert "<agent-name>" in err

def test_init_invalid_name_rejected(tmp_path):
    invalid_names = ["_invalid-name", "My Agent", "MyAgent"]
    for name in invalid_names:
        code, out, err = run_cli(["init", name], cwd=tmp_path)
        assert code != 0
        assert "Invalid agent name" in err

def test_cli_installable_and_runnable():
    # Simulate install and help
    import subprocess
    result = subprocess.run([sys.executable, "-m", "kinnoo.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "init" in result.stdout


def test_init_creates_directory_structure(tmp_path):
    agent_name = "test-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None  # dry-run or success
    agent_dir = tmp_path / agent_name
    assert agent_dir.exists() and agent_dir.is_dir()
    expected_files = ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]
    for fname in expected_files:
        assert (agent_dir / fname).exists()
    assert (agent_dir / "tools").is_dir()
    assert (agent_dir / "prompts").is_dir()


def test_generated_manifest_passes_validation(tmp_path):
    agent_name = "test-agent"
    run_cli(["init", agent_name], cwd=tmp_path)
    from kinnoo.validator import validate
    manifest_path = tmp_path / agent_name / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid
    assert not errors


def test_generated_entrypoint_executes(tmp_path):
    agent_name = "test-agent"
    run_cli(["init", agent_name], cwd=tmp_path)
    run_py = tmp_path / agent_name / "run.py"
    result = subprocess.run([sys.executable, str(run_py), "hello"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout


def test_generated_entrypoint_has_asyncio(tmp_path):
    agent_name = "test-agent"
    run_cli(["init", agent_name], cwd=tmp_path)
    run_py = tmp_path / agent_name / "run.py"
    contents = run_py.read_text()
    assert "asyncio.run" in contents
    assert "async def" in contents


def test_init_existing_directory_fails(tmp_path):
    agent_name = "test-agent"
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code != 0
    assert "already exists" in err
    # Directory should be unchanged (still exists)
    assert agent_dir.exists() and agent_dir.is_dir()


def test_init_full_workflow(tmp_path):
    agent_name = "my-first-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    # Directory and files exist
    assert agent_dir.exists() and agent_dir.is_dir()
    for fname in ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]:
        assert (agent_dir / fname).exists()
    assert (agent_dir / "tools").is_dir()
    assert (agent_dir / "prompts").is_dir()
    # Manifest passes validation
    from kinnoo.validator import validate
    manifest_path = agent_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid
    assert not errors
    # Entrypoint runs successfully
    run_py = agent_dir / "run.py"
    result = subprocess.run([sys.executable, str(run_py), "test"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout
