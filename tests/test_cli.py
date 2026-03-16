import subprocess
import sys
import pytest
import re
import types

def test_cli_installable_and_runnable():
    # This test checks that the CLI is installable and runnable via pyproject.toml
    result = subprocess.run([sys.executable, "-m", "kinnoo.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "init" in result.stdout


def test_cli_version_flag():
    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    output = result.stdout.strip()
    assert re.search(r"\b\d+\.\d+\.\d+\b", output), f"Expected semantic version in output, got: {output!r}"


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


def test_run_without_input_defaults_to_required(tmp_path):
    agent_dir = tmp_path / "feature20-default-required-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    # Intentionally omit inputs.required so default behavior remains input-required.
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: default-required-agent
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
    (agent_dir / "run.py").write_text("print('should not run without input')\n")
    (agent_dir / "README.md").write_text("feature20 default-required test")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(agent_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "input is required for kinnoo run unless --preflight is used" in result.stderr


def test_run_without_input_allowed_when_inputs_not_required(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_agent(**kwargs):
        captured.update(kwargs)
        return 0

    fake_module = types.SimpleNamespace(run_agent=fake_run_agent)
    monkeypatch.setitem(sys.modules, "kinnoo.run_command", fake_module)

    from kinnoo.cli import main

    agent_dir = tmp_path / "feature20-no-input-agent"
    agent_dir.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        ["kinnoo", "run", str(agent_dir)],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    assert captured["agent_dir_arg"] == str(agent_dir)
    assert captured["input_arg"] is None
    assert captured["pass_through_args"] == []


def test_run_pass_through_args_forwarded_verbatim(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_run_agent(**kwargs):
        captured.update(kwargs)
        return 0

    fake_module = types.SimpleNamespace(run_agent=fake_run_agent)
    monkeypatch.setitem(sys.modules, "kinnoo.run_command", fake_module)

    from kinnoo.cli import main

    agent_dir = tmp_path / "feature20-pass-through-agent"
    agent_dir.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kinnoo",
            "run",
            str(agent_dir),
            "--",
            "-e",
            "text",
            "-u",
            "https://example.com",
            "-p",
            "./file.txt",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    assert captured["input_arg"] is None
    assert captured["pass_through_args"] == [
        "-e",
        "text",
        "-u",
        "https://example.com",
        "-p",
        "./file.txt",
    ]


def test_run_single_input_backward_compatible(tmp_path):
    agent_dir = tmp_path / "feature20-single-input-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature20-single-input-agent
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
    (agent_dir / "run.py").write_text(
        'import sys\nprint(f"input: {sys.argv[1] if len(sys.argv) > 1 else \"\"}")\n'
    )
    (agent_dir / "README.md").write_text("feature20 backward-compat test")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"kinnoo run failed: {result.stderr}"
    assert "input: hello" in result.stdout or "input: hello" in result.stderr


def test_run_without_input_rejected_when_required(tmp_path):
    agent_dir = tmp_path / "feature20-required-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature20-required-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
    required: true
outputs:
    type: text
"""
    )
    (agent_dir / "run.py").write_text("print('should not run')\n")
    (agent_dir / "README.md").write_text("feature20 required-input test")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(agent_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "input is required" in result.stderr


def test_run_no_input_and_pass_through_modes_both_supported(tmp_path):
    no_input_agent = tmp_path / "feature20-no-input-agent"
    no_input_agent.mkdir()
    (no_input_agent / "requirements.txt").write_text("")
    (no_input_agent / "kinnoo.yaml").write_text(
        """
name: feature20-no-input-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
    required: false
outputs:
    type: text
"""
    )
    (no_input_agent / "run.py").write_text(
        "import sys\nprint('ARGS:' + '|'.join(sys.argv[1:]))\n"
    )
    (no_input_agent / "README.md").write_text("feature20 no-input mode")
    (no_input_agent / "tools").mkdir()
    (no_input_agent / "prompts").mkdir()

    no_input_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(no_input_agent)],
        capture_output=True,
        text=True,
    )
    assert no_input_result.returncode == 0, no_input_result.stderr
    assert "ARGS:" in no_input_result.stdout

    pass_through_agent = tmp_path / "feature20-pass-through-agent"
    pass_through_agent.mkdir()
    (pass_through_agent / "requirements.txt").write_text("")
    (pass_through_agent / "kinnoo.yaml").write_text(
        """
name: feature20-pass-through-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
    required: false
outputs:
    type: text
"""
    )
    (pass_through_agent / "run.py").write_text(
        "import sys\nprint('ARGS:' + '|'.join(sys.argv[1:]))\n"
    )
    (pass_through_agent / "README.md").write_text("feature20 pass-through mode")
    (pass_through_agent / "tools").mkdir()
    (pass_through_agent / "prompts").mkdir()

    pass_through_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(pass_through_agent),
            "--",
            "-e",
            "text",
            "-u",
            "https://example.com",
            "-p",
            "./file.txt",
        ],
        capture_output=True,
        text=True,
    )
    assert pass_through_result.returncode == 0, pass_through_result.stderr
    assert "ARGS:-e|text|-u|https://example.com|-p|./file.txt" in pass_through_result.stdout


def test_run_required_input_cannot_be_bypassed_by_pass_through(tmp_path):
    agent_dir = tmp_path / "feature20-required-pass-through-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature20-required-pass-through-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
    required: true
outputs:
    type: text
"""
    )
    (agent_dir / "run.py").write_text("print('should not run with bypass attempt')\n")
    (agent_dir / "README.md").write_text("feature20 required bypass guard test")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "--",
            "-e",
            "text",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "input is required" in result.stderr
    assert "should not run" not in result.stdout


def test_run_usage_includes_feature20_modes():
    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Usage: kinnoo run <agent-dir> '<input>'" in result.stderr
    assert "kinnoo run <agent-dir>" in result.stderr
    assert "kinnoo run <agent-dir> -- <args...>" in result.stderr


def test_run_help_includes_pass_through_separator_usage():
    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "kinnoo run <agent-dir> -- -e <some-string> -p <some-file-path> -u <some-url>" in result.stdout


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


def _run_feature21_smoke_framework(tmp_path, framework: str, marker: str):
    agent_name = f"feature21-smoke-{framework}"
    init_result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "init", agent_name, "--framework", framework],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert init_result.returncode == 0, init_result.stderr

    agent_dir = tmp_path / agent_name
    # Keep smoke runs deterministic and network-independent in CI.
    (agent_dir / "requirements.txt").write_text("")

    run_result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert run_result.returncode == 0, run_result.stderr
    assert run_result.stdout.strip() != ""
    assert marker in run_result.stdout
    assert "Traceback" not in run_result.stderr
    assert "Error:" not in run_result.stderr


def test_feature21_pydanticai_smoke_run(tmp_path):
    _run_feature21_smoke_framework(
        tmp_path=tmp_path,
        framework="pydantic-ai",
        marker="[pydantic-ai template]",
    )


def test_feature21_langgraph_smoke_run(tmp_path):
    _run_feature21_smoke_framework(
        tmp_path=tmp_path,
        framework="langgraph",
        marker="[langgraph template]",
    )


def test_feature21_openai_agents_smoke_run(tmp_path):
    _run_feature21_smoke_framework(
        tmp_path=tmp_path,
        framework="openai-agents",
        marker="[openai-agents template]",
    )


def test_feature21_pydantic_ai_basic_run(tmp_path):
    cli_path = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    agent_name = "feature21-pydantic-ai-basic-run"
    init_result = subprocess.run(
        [sys.executable, str(cli_path), "init", agent_name, "--framework", "pydantic-ai"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert init_result.returncode == 0, init_result.stderr

    agent_dir = tmp_path / agent_name
    # Keep task131 run deterministic and network-independent.
    (agent_dir / "requirements.txt").write_text("")

    env = os.environ.copy()
    env["KINNOO_TEST_SAFE_MODE"] = "1"

    run_result = subprocess.run(
        [sys.executable, str(cli_path), "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    assert run_result.returncode == 0, run_result.stderr
    assert run_result.stdout.strip() != ""
    assert "[pydantic-ai template] test-safe response: hello" in run_result.stdout
    assert "Traceback" not in run_result.stderr


def test_feature21_langgraph_basic_run(tmp_path):
    cli_path = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    agent_name = "feature21-langgraph-basic-run"
    init_result = subprocess.run(
        [sys.executable, str(cli_path), "init", agent_name, "--framework", "langgraph"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert init_result.returncode == 0, init_result.stderr

    agent_dir = tmp_path / agent_name
    # Keep task132 run deterministic and network-independent.
    (agent_dir / "requirements.txt").write_text("")

    env = os.environ.copy()
    env["KINNOO_TEST_SAFE_MODE"] = "1"

    run_result = subprocess.run(
        [sys.executable, str(cli_path), "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    assert run_result.returncode == 0, run_result.stderr
    assert run_result.stdout.strip() != ""
    assert "[langgraph template] test-safe response: hello" in run_result.stdout
    assert "Traceback" not in run_result.stderr


def test_feature21_openai_agents_basic_run(tmp_path):
    cli_path = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    agent_name = "feature21-openai-agents-basic-run"
    init_result = subprocess.run(
        [sys.executable, str(cli_path), "init", agent_name, "--framework", "openai-agents"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert init_result.returncode == 0, init_result.stderr

    agent_dir = tmp_path / agent_name
    # Keep task133 run deterministic and network-independent.
    (agent_dir / "requirements.txt").write_text("")

    env = os.environ.copy()
    env["KINNOO_TEST_SAFE_MODE"] = "1"

    run_result = subprocess.run(
        [sys.executable, str(cli_path), "run", str(agent_dir), "hello"],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    assert run_result.returncode == 0, run_result.stderr
    assert run_result.stdout.strip() != ""
    assert "[openai-agents template] test-safe response: hello" in run_result.stdout
    assert "Traceback" not in run_result.stderr
