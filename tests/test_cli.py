import subprocess
import sys
import pytest
import re
import types
import time
import signal
import json

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


def _feature23_write_server_fixture(tmp_path, script_name: str = "feature23_server.py"):
    server_script = tmp_path / script_name
    server_script.write_text(
        """
import socket
import sys
import time

mode = sys.argv[1]

if mode == "tcp":
    port = int(sys.argv[2])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", port))
    s.listen(1)
    print(f"TCP_READY:{port}", flush=True)
    time.sleep(1.2)
    s.close()
elif mode == "stdout":
    marker = sys.argv[2]
    time.sleep(0.15)
    print(marker, flush=True)
    time.sleep(0.9)
elif mode == "silent":
    time.sleep(0.8)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return server_script


def test_feature23_readiness_probe_tcp_and_stdout_marker(tmp_path):
    from kinnoo.supervisor import (
        infer_readiness_config,
        shutdown_server,
        start_server,
        stream_output,
        wait_until_ready,
    )

    server_script = _feature23_write_server_fixture(tmp_path)

    tcp_port = 48651
    tcp_runtime = {
        "readiness_probe": {
            "method": "tcp",
            "port": tcp_port,
        }
    }
    tcp_process = start_server([sys.executable, str(server_script), "tcp", str(tcp_port)])
    try:
        tcp_stream_state = stream_output(tcp_process)
        tcp_ready = wait_until_ready(
            tcp_process,
            infer_readiness_config(tcp_runtime),
            tcp_stream_state,
        )
        assert tcp_ready is True
    finally:
        shutdown_server(tcp_process)

    stdout_marker = "READY_MARKER_142"
    stdout_runtime = {
        "readiness_probe": {
            "method": "stdout",
            "marker": stdout_marker,
        }
    }
    stdout_process = start_server([sys.executable, str(server_script), "stdout", stdout_marker])
    try:
        stdout_stream_state = stream_output(stdout_process)
        stdout_ready = wait_until_ready(
            stdout_process,
            infer_readiness_config(stdout_runtime),
            stdout_stream_state,
        )
        assert stdout_ready is True
    finally:
        shutdown_server(stdout_process)

    failing_stdout_runtime = {
        "readiness_probe": {
            "method": "stdout",
            "marker": "THIS_MARKER_NEVER_APPEARS",
        }
    }
    failing_process = start_server([sys.executable, str(server_script), "silent"])
    try:
        failing_stream_state = stream_output(failing_process)
        failing_readiness = infer_readiness_config(failing_stdout_runtime)
        failing_readiness.timeout_seconds = 0.25
        failed_ready = wait_until_ready(
            failing_process,
            failing_readiness,
            failing_stream_state,
        )
        assert failed_ready is False
    finally:
        shutdown_server(failing_process)


def test_feature23_default_readiness_fallback_behavior(tmp_path):
    from kinnoo.supervisor import (
        infer_readiness_config,
        shutdown_server,
        start_server,
        stream_output,
        wait_until_ready,
    )

    server_script = _feature23_write_server_fixture(tmp_path)

    tcp_port = 48652
    runtime_with_port = {"port": tcp_port}
    readiness_with_port = infer_readiness_config(runtime_with_port)
    assert readiness_with_port.mode == "tcp"
    assert readiness_with_port.port == tcp_port

    tcp_process = start_server([sys.executable, str(server_script), "tcp", str(tcp_port)])
    try:
        tcp_stream_state = stream_output(tcp_process)
        tcp_ready = wait_until_ready(tcp_process, readiness_with_port, tcp_stream_state)
        assert tcp_ready is True
    finally:
        shutdown_server(tcp_process)

    runtime_without_probe_or_port = {}
    readiness_without_probe_or_port = infer_readiness_config(runtime_without_probe_or_port)
    assert readiness_without_probe_or_port.mode == "immediate"

    immediate_process = start_server([sys.executable, str(server_script), "silent"])
    try:
        immediate_stream_state = stream_output(immediate_process)
        immediate_ready = wait_until_ready(
            immediate_process,
            readiness_without_probe_or_port,
            immediate_stream_state,
        )
        assert immediate_ready is True
    finally:
        shutdown_server(immediate_process)


def _feature23_write_mcp_agent_fixture(tmp_path, script_name: str = "feature23_mcp_agent.py"):
    agent_dir = tmp_path / "feature23-mcp-agent"
    agent_dir.mkdir()
    agent_script = agent_dir / script_name
    agent_script.write_text(
        """
import signal
import sys
import time

mode = sys.argv[1] if len(sys.argv) > 1 else "normal"
running = True

def _stop(*_args):
    global running
    running = False

signal.signal(signal.SIGTERM, _stop)

print("SERVER_READY", flush=True)
print("server-stderr-start", file=sys.stderr, flush=True)
counter = 0
while running:
    print(f"server-stdout-tick:{counter}", flush=True)
    print(f"server-stderr-tick:{counter}", file=sys.stderr, flush=True)
    counter += 1
    time.sleep(0.1)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "README.md").write_text("feature23 mcp fixture", encoding="utf-8")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: feature23-mcp-agent
version: 0.1.0
entrypoint: {script_name}
runtime:
    language: python
    version: ">=3.10"
    type: mcp-server
    readiness_probe:
        method: stdout
        marker: SERVER_READY
dependencies: []
inputs:
    type: text
    required: false
outputs:
    type: text
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return agent_dir


def test_feature23_run_mcp_server_long_running_mode(tmp_path):
    cli_path = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    agent_dir = _feature23_write_mcp_agent_fixture(tmp_path)

    process = subprocess.Popen(
        [sys.executable, str(cli_path), "run", str(agent_dir)],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(0.5)
        assert process.poll() is None, "mcp-server runtime exited too early"
    finally:
        process.terminate()
        process.wait(timeout=3)


def test_feature23_mcp_server_streams_stdout_stderr(tmp_path):
    cli_path = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    agent_dir = _feature23_write_mcp_agent_fixture(tmp_path)

    process = subprocess.Popen(
        [sys.executable, str(cli_path), "run", str(agent_dir)],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    saw_stdout_stream = False
    saw_stderr_stream = False
    start = time.monotonic()

    try:
        while (time.monotonic() - start) < 3.0 and (not saw_stdout_stream or not saw_stderr_stream):
            if not saw_stdout_stream and process.stdout is not None:
                line = process.stdout.readline()
                if line:
                    stdout_lines.append(line)
                    if "server-stdout" in line:
                        saw_stdout_stream = True
            if not saw_stderr_stream and process.stderr is not None:
                line = process.stderr.readline()
                if line:
                    stderr_lines.append(line)
                    if "server-stderr" in line:
                        saw_stderr_stream = True
            if process.poll() is not None:
                break

        assert process.poll() is None, "mcp-server process ended before streaming assertions"
        assert saw_stdout_stream, f"Expected server stdout streaming line in: {stdout_lines!r}"
        assert saw_stderr_stream, f"Expected server stderr streaming line in: {stderr_lines!r}"
    finally:
        process.terminate()
        process.wait(timeout=3)


def _feature23_write_stubborn_mcp_agent_fixture(tmp_path, script_name: str = "feature23_stubborn_mcp.py"):
    agent_dir = tmp_path / "feature23-stubborn-mcp-agent"
    agent_dir.mkdir()
    marker_file = agent_dir / "term-marker.txt"
    agent_script = agent_dir / script_name
    agent_script.write_text(
        f"""
import signal
import time
from pathlib import Path

marker_file = Path(r"{marker_file}")

def _on_sigterm(*_args):
    marker_file.write_text("SIGTERM_RECEIVED", encoding="utf-8")
    print("SIGTERM_RECEIVED", flush=True)

signal.signal(signal.SIGTERM, _on_sigterm)
print("SERVER_READY", flush=True)
while True:
    time.sleep(0.1)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "README.md").write_text("feature23 stubborn mcp fixture", encoding="utf-8")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: feature23-stubborn-mcp-agent
version: 0.1.0
entrypoint: {script_name}
runtime:
    language: python
    version: ">=3.10"
    type: mcp-server
    shutdown_timeout_seconds: 0.25
    readiness_probe:
        method: stdout
        marker: SERVER_READY
dependencies: []
inputs:
    type: text
    required: false
outputs:
    type: text
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return agent_dir, marker_file


def test_feature23_sigint_graceful_shutdown_with_escalation(tmp_path):
    agent_dir, marker_file = _feature23_write_stubborn_mcp_agent_fixture(tmp_path)

    cli_path = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")

    process = subprocess.Popen(
        [sys.executable, str(cli_path), "run", str(agent_dir)],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    logs_dir = tmp_path / ".kinnoo" / "logs"
    try:
        ready_seen = False
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and not ready_seen:
            if process.stdout is not None:
                line = process.stdout.readline()
                if "SERVER_READY" in line:
                    ready_seen = True
            if process.poll() is not None:
                break

        assert ready_seen, "mcp-server fixture did not reach ready state before SIGINT"

        process.send_signal(signal.SIGINT)
        process.wait(timeout=6)

        assert process.returncode != 0
        assert marker_file.exists(), "Expected SIGTERM handler marker file to verify SIGTERM-first shutdown"

        log_files = sorted(logs_dir.glob("run.*.log"))
        assert log_files, f"Expected run trace log in {logs_dir}"
        payload = json.loads(log_files[-1].read_text(encoding="utf-8"))

        assert payload["runtime_type"] == "mcp-server"
        assert payload.get("shutdown_sigterm_sent") is True
        assert payload.get("shutdown_sigkill_sent") is True
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=3)
