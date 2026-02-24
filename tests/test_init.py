def test_framework_templates_generate_correct_files():
    import tempfile
    from pathlib import Path
    frameworks = [
        ("gemini", "google-generativeai", "GOOGLE_API_KEY", "Hello Gemini!", "gemini-pro"),
        ("chatgpt", "openai", "OPENAI_API_KEY", "Hello ChatGPT!", "gpt-3.5-turbo"),
        ("claude-chat", "anthropic", "ANTHROPIC_API_KEY", "Hello Claude!", "claude-3-opus-20240229"),
    ]
    for fw, dep, envvar, run_example, model_hint in frameworks:
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_name = f"test_{fw}"
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = run_kinnoo_init([agent_name, "--framework", fw])
            finally:
                os.chdir(cwd)
            assert result.returncode == 0, f"Framework {fw} should succeed"
            agent_dir = Path(tmpdir) / agent_name
            # Directory and files
            assert agent_dir.exists()
            for fname in ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]:
                assert (agent_dir / fname).exists(), f"{fname} missing for {fw}"
            # requirements.txt
            reqs = (agent_dir / "requirements.txt").read_text()
            assert dep in reqs, f"Dependency {dep} missing in requirements.txt for {fw}"
            # README.md
            readme = (agent_dir / "README.md").read_text()
            assert envvar in readme, f"API key env var {envvar} missing in README for {fw}"
            assert run_example in readme, f"Run example missing in README for {fw}"
            # run.py
            runpy = (agent_dir / "run.py").read_text()
            assert model_hint in runpy, f"Model hint {model_hint} missing in run.py for {fw}"
            # tools/ and prompts/
            assert (agent_dir / "tools").is_dir()
            assert (agent_dir / "prompts").is_dir()
import os
import shutil
import subprocess
import tempfile
import sys

KINNOO_INIT_PATH = os.path.join(os.path.dirname(__file__), '../src/kinnoo/init_command.py')

def run_kinnoo_init(args):
    cmd = [sys.executable, KINNOO_INIT_PATH] + args
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result

def test_framework_valid():
    # Should not error for supported frameworks (no file creation yet)
    import tempfile
    for fw in ["gemini", "chatgpt", "claude-chat"]:
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_name = f"myagent_{fw}"
            cwd = os.getcwd()
            os.chdir(tmpdir)
            result = run_kinnoo_init([agent_name, "--framework", fw])
            os.chdir(cwd)
            assert result.returncode == 0, f"Valid framework {fw} should not error"

def test_framework_invalid():
    # Should error for unsupported frameworks
    for fw in ["langgraph", "pigglypoo", "openai"]:
        result = run_kinnoo_init(["myagent", "--framework", fw])
        assert result.returncode != 0, f"Invalid framework {fw} should error"
        assert b"Unsupported framework" in result.stderr, f"Error message missing for {fw}"
        assert b"Usage: kinnoo init" in result.stderr, f"Usage message missing for {fw}"

def test_missing_agent_name():
    # Should error and print usage if agent_name is missing
    result = run_kinnoo_init(["--framework", "gemini"])
    assert result.returncode != 0, "Missing agent_name should error"
    assert b"Usage: kinnoo init" in result.stderr, "Usage message missing for missing agent_name"
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


def test_framework_manifests_pass_validation():
    import tempfile
    from pathlib import Path
    from kinnoo.validator import validate
    frameworks = ["gemini", "chatgpt", "claude-chat"]
    for fw in frameworks:
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_name = f"validate-{fw}"
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = run_kinnoo_init([agent_name, "--framework", fw])
                assert result.returncode == 0, f"Framework {fw} should succeed"
                manifest_path = Path(tmpdir) / agent_name / "kinnoo.yaml"
                is_valid, errors = validate(str(manifest_path))
                assert is_valid, f"Manifest for {fw} should be valid, got errors: {errors}"
                assert not errors, f"Manifest for {fw} should have no errors, got: {errors}"
            finally:
                os.chdir(cwd)


def test_init_vanilla_agent(tmp_path):
    agent_name = "vanilla-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    assert agent_dir.exists() and agent_dir.is_dir()
    # requirements.txt should be empty (vanilla agent)
    reqs = (agent_dir / "requirements.txt").read_text()
    assert reqs.strip() == ""
    # README.md should not mention any API key
    readme = (agent_dir / "README.md").read_text()
    assert "API key" not in readme
    # run.py should be the hello-world template
    runpy = (agent_dir / "run.py").read_text()
    assert "Hello, world!" in runpy
