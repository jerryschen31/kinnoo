import subprocess
import sys
import pytest
import re
import types
import time
import signal
import json
import zipfile
import shutil
from pathlib import Path

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


def test_top_level_help_grouped_menu_exact_text():
    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    output = result.stdout
    assert "Kinnoo CLI" in output
    assert "all agents:" in output
    assert "{init,run,test,install,pack,inspect, import,check}" in output
    assert "test                Execute standardized declarative tests for an agent" in output
    assert "daemon agents:" in output
    assert "{stop,attach,logs}" in output
    assert "registry:" in output
    assert "{publish,install,list,search,sync,login,logout}" in output
    assert "sync                Sync source metadata into local registry mirror" in output
    assert "other:" in output
    assert "{keygen}" in output
    assert "--version" in output


def test_top_level_help_colored_when_forced():
    env = dict(os.environ)
    env["KINNOO_FORCE_COLOR"] = "1"

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "-h"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert "\u001b[" in result.stdout
    assert "Kinnoo CLI" in result.stdout
    assert "all agents:" in result.stdout
    assert "\u001b[1m\u001b[34musage:\u001b[0m" in result.stdout
    assert "\u001b[1m\u001b[35mkinnoo\u001b[0m" in result.stdout
    assert "\u001b[1m\u001b[36m--version\u001b[0m" in result.stdout
    assert "\u001b[1m\u001b[36m--help\u001b[0m" in result.stdout
    assert "\u001b[1m\u001b[32minit\u001b[0m" in result.stdout
    assert "\u001b[1m\u001b[32m{init,run,test,install,pack,inspect, import,check}\u001b[0m" in result.stdout


def test_backend_selection(monkeypatch, tmp_path):
    from kinnoo import install_command, publish_command
    from kinnoo.config import PublishBehaviorConfig

    archive_root = tmp_path / "archive"
    agent_archive_dir = archive_root / "demo-agent" / "1.0.0"
    agent_archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = agent_archive_dir / "demo-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "kinnoo.yaml",
            (
                "name: demo-agent\n"
                "version: 1.0.0\n"
                "entrypoint: run.py\n"
                "runtime:\n"
                "  language: python\n"
                "  version: \">=3.10\"\n"
                "  type: one-shot\n"
                "dependencies: []\n"
                "inputs:\n"
                "  type: text\n"
                "outputs:\n"
                "  type: text\n"
            ),
        )
        archive_zip.writestr("run.py", "print('ok')\n")
        archive_zip.writestr("requirements.txt", "")

    monkeypatch.setenv("KINNOO_ARCHIVE_ROOT", str(archive_root))

    captured_publish: list[str] = []

    def _fake_publish_validated_archive(**kwargs):
        captured_publish.append(str(kwargs["backend_label"]))
        return 0

    monkeypatch.setattr(
        publish_command,
        "_publish_validated_archive",
        _fake_publish_validated_archive,
    )
    monkeypatch.setattr(
        publish_command,
        "load_publish_behavior_config",
        lambda: PublishBehaviorConfig(publish_to_authenticated_registry=False),
    )

    monkeypatch.delenv("KINNOO_REGISTRY_URL", raising=False)
    monkeypatch.delenv("KINNOO_REGISTRY_TOKEN", raising=False)
    monkeypatch.delenv("KINNOO_TENANT_SLUG", raising=False)

    local_publish_exit = publish_command.publish_agent(
        agent_name="demo-agent",
        use_local=False,
        use_remote=False,
    )
    assert local_publish_exit == 0
    assert captured_publish[-1] == "local"

    monkeypatch.setenv("KINNOO_REGISTRY_URL", "https://registry.example.test")
    monkeypatch.setenv("KINNOO_REGISTRY_TOKEN", "token")
    monkeypatch.setenv("KINNOO_TENANT_SLUG", "acme")

    remote_publish_exit = publish_command.publish_agent(
        agent_name="demo-agent",
        use_local=False,
        use_remote=False,
    )
    assert remote_publish_exit == 0
    assert captured_publish[-1] == "remote"

    selected_backends: list[str] = []

    class _FakeLocalBackend:
        def __init__(self, *args, **kwargs):
            del args, kwargs

    class _FakeRemoteBackend:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def resolve(self, *, name, version=None, tenant=None):
            del name, version, tenant
            return {"download_url": "https://registry.example.test/demo-agent.kno"}

    class _FakeRegistryService:
        def __init__(self, backend):
            if isinstance(backend, _FakeRemoteBackend):
                selected_backends.append("remote")
            else:
                selected_backends.append("local")

        def resolve_with_error(self, *, name, version=None):
            del name, version
            return (
                RegistryRecord(
                    name="demo-agent",
                    version="1.0.0",
                    archive_path=archive_path,
                ),
                None,
            )

    def _fake_parse_install_target_spec(_target: str) -> InstallTargetSpec:
        return InstallTargetSpec(
            kind="registry-latest",
            raw_target="demo-agent",
            name="demo-agent",
        )

    class _FakeHTTPResponse:
        def __init__(self, payload: bytes):
            self._payload = payload

        def read(self) -> bytes:
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            del exc_type, exc_val, exc_tb
            return None

    def _fake_urlopen(_url, timeout=30):
        del timeout
        with archive_path.open("rb") as archive_file:
            return _FakeHTTPResponse(archive_file.read())

    monkeypatch.setattr(install_command, "MockFilesystemRegistryBackend", _FakeLocalBackend)
    monkeypatch.setattr(install_command, "RemoteRegistryClient", _FakeRemoteBackend)
    monkeypatch.setattr(install_command, "RegistryService", _FakeRegistryService)
    monkeypatch.setattr(install_command, "parse_install_target_spec", _fake_parse_install_target_spec)
    monkeypatch.setattr(install_command, "_install_from_archive_path", lambda **kwargs: 0)
    monkeypatch.setattr(install_command.urllib_request, "urlopen", _fake_urlopen)

    install_local_exit = install_command.install_agent(
        archive_path="demo-agent",
        target_dir_arg=str(tmp_path / "installed-local"),
        assume_yes=True,
        use_local=True,
        use_remote=False,
    )
    assert install_local_exit == 0
    assert selected_backends[-1] == "local"

    install_remote_exit = install_command.install_agent(
        archive_path="demo-agent",
        target_dir_arg=str(tmp_path / "installed-remote"),
        assume_yes=True,
        use_local=False,
        use_remote=True,
    )
    assert install_remote_exit == 0
    assert selected_backends[-1] == "remote"


def test_feature69_standardized_tests_file_parser(tmp_path):
    agent_dir = tmp_path / "feature69-parser-agent"
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature69-parser-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.10\"",
                "  type: one-shot",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

    # Canonical external test file path.
    (agent_dir / "kinnoo.tests.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "tests:",
                "  - id: smoke-1",
                "    name: basic parse",
                "    input: hello",
                "    assertions:",
                "      - contains: ok",
                "    timeout_seconds: 5",
                "    expected_exit_code: 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    valid_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "test",
            str(agent_dir),
            "--validate-only",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert valid_result.returncode == 0
    valid_payload = json.loads(valid_result.stdout)
    assert valid_payload["valid"] is True
    assert valid_payload["total"] == 1
    assert valid_payload["source"].endswith("kinnoo.tests.yaml")

    (agent_dir / "kinnoo.tests.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "tests:",
                "  - id: bad-1",
                "    name: invalid fixture",
                "    input: hello",
                "    timeout_seconds: 3",
                "    expected_exit_code: 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    invalid_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "test",
            str(agent_dir),
            "--validate-only",
        ],
        capture_output=True,
        text=True,
    )
    assert invalid_result.returncode == 1
    assert "Missing required field: tests[0].assertions" in invalid_result.stdout

    # Remove canonical file to validate inline compatibility bridge from kinnoo.yaml.
    (agent_dir / "kinnoo.tests.yaml").unlink()
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature69-parser-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.10\"",
                "  type: one-shot",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
                "tests_version: 1",
                "tests:",
                "  - id: inline-1",
                "    name: inline declaration",
                "    input: ping",
                "    assertions:",
                "      - contains: pong",
                "    timeout_seconds: 4",
                "    expected_exit_code: 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    inline_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "test",
            str(agent_dir),
            "--validate-only",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert inline_result.returncode == 0
    inline_payload = json.loads(inline_result.stdout)
    assert inline_payload["valid"] is True
    assert inline_payload["total"] == 1
    assert inline_payload["source"].endswith("kinnoo.yaml")


def test_feature69_execution_engine_and_docs_examples(tmp_path):
    one_shot_dir = tmp_path / "feature69-oneshot"
    one_shot_dir.mkdir()
    (one_shot_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature69-oneshot",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.10\"",
                "  type: one-shot",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (one_shot_dir / "run.py").write_text(
        "import sys\n"
        "print(f'oneshot:{sys.argv[1]}')\n",
        encoding="utf-8",
    )
    (one_shot_dir / "kinnoo.tests.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "tests:",
                "  - id: oneshot-1",
                "    name: one-shot pass",
                "    input: ping",
                "    assertions:",
                "      - contains: oneshot:ping",
                "    timeout_seconds: 5",
                "    expected_exit_code: 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    one_shot_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "test", str(one_shot_dir), "--json"],
        capture_output=True,
        text=True,
    )
    assert one_shot_result.returncode == 0
    one_shot_payload = json.loads(one_shot_result.stdout)
    assert one_shot_payload["passed"] == 1
    assert one_shot_payload["total"] == 1
    assert one_shot_payload["results"][0]["runtime_type"] == "one-shot"
    assert one_shot_payload["results"][0]["status"] == "passed"

    daemon_dir = tmp_path / "feature69-daemon"
    daemon_dir.mkdir()
    (daemon_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature69-daemon",
                "version: 1.0.0",
                "entrypoint: daemon.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.10\"",
                "  type: daemon",
                "  run_command: \"python3 daemon.py\"",
                "dependencies: []",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (daemon_dir / "daemon.py").write_text(
        "import sys\n"
        "print(f'daemon:{sys.argv[1]}')\n",
        encoding="utf-8",
    )
    (daemon_dir / "kinnoo.tests.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "tests:",
                "  - id: daemon-1",
                "    name: daemon pass",
                "    input: pong",
                "    assertions:",
                "      - contains: daemon:pong",
                "    timeout_seconds: 5",
                "    expected_exit_code: 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    daemon_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "test", str(daemon_dir), "--json"],
        capture_output=True,
        text=True,
    )
    assert daemon_result.returncode == 0
    daemon_payload = json.loads(daemon_result.stdout)
    assert daemon_payload["passed"] == 1
    assert daemon_payload["total"] == 1
    assert daemon_payload["results"][0]["runtime_type"] == "daemon"
    assert daemon_payload["results"][0]["status"] == "passed"

    repo_root = Path(__file__).resolve().parents[1]
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    schema_text = (repo_root / "docs" / "manifest-schema-reference.md").read_text(encoding="utf-8")
    combined_docs = f"{readme_text}\n{schema_text}"

    assert "Feature69 kinnoo test command" in combined_docs
    assert "kinnoo.tests.yaml" in combined_docs
    assert "kinnoo test ./my-agent" in combined_docs
    assert "type: one-shot" in combined_docs
    assert "type: daemon" in combined_docs


def test_publish_toggle_true_prefers_authenticated_remote(monkeypatch, tmp_path):
    from kinnoo import publish_command

    (tmp_path / "kinnoo-config.txt").write_text(
        "publish_to_authenticated_registry=true\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("KINNOO_REGISTRY_URL", "https://registry.example.test")
    monkeypatch.delenv("KINNOO_REGISTRY_TOKEN", raising=False)
    monkeypatch.delenv("KINNOO_TENANT_SLUG", raising=False)

    captured_remote_kwargs: dict[str, str] = {}

    class _FakeRemoteBackend:
        def __init__(self, *, base_url, token, tenant_slug):
            captured_remote_kwargs["base_url"] = base_url
            captured_remote_kwargs["token"] = token
            captured_remote_kwargs["tenant_slug"] = tenant_slug

    monkeypatch.setattr(publish_command, "RemoteRegistryClient", _FakeRemoteBackend)
    monkeypatch.setattr(
        publish_command,
        "_issue_registry_token_with_admin_credentials",
        lambda *, config: ("issued-admin-token", "global"),
    )

    backend, backend_label, backend_error = publish_command._resolve_publish_backend(
        use_local=False,
        use_remote=False,
    )

    assert backend_error is None
    assert backend_label == "remote"
    assert isinstance(backend, _FakeRemoteBackend)
    assert captured_remote_kwargs == {
        "base_url": "https://registry.example.test",
        "token": "issued-admin-token",
        "tenant_slug": "global",
    }


def test_publish_toggle_false_keeps_current_local_default(monkeypatch, tmp_path):
    from kinnoo import publish_command

    (tmp_path / "kinnoo-config.txt").write_text(
        "publish_to_authenticated_registry=false\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KINNOO_REGISTRY_URL", raising=False)
    monkeypatch.delenv("KINNOO_REGISTRY_TOKEN", raising=False)
    monkeypatch.delenv("KINNOO_TENANT_SLUG", raising=False)

    backend, backend_label, backend_error = publish_command._resolve_publish_backend(
        use_local=False,
        use_remote=False,
    )

    assert backend_error is None
    assert backend_label == "local"


import tempfile
import shutil
import os
import sys
import venv
from pathlib import Path
from kinnoo.registry import InstallTargetSpec, RegistryRecord


CLI_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"

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
        'import sys\nprint(f"input: {sys.argv[1] if len(sys.argv) > 1 else \'\'}")\n'
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
    assert "kinnoo run <agent-dir> --json-input '<json>'" in result.stderr
    assert "kinnoo run <agent-dir> --json-file <json-file>" in result.stderr
    assert "kinnoo run <agent-dir> -- <args...>" in result.stderr


def test_run_help_includes_pass_through_separator_usage():
    result = subprocess.run(
        [sys.executable, "-m", "kinnoo.cli", "run", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "kinnoo run <agent-dir> -- -e <some-string> -p <some-file-path> -u <some-url>" in result.stdout


def _discover_alternate_python_interpreter() -> tuple[str, tuple[int, int]] | None:
    """Find a python executable with a different major.minor than the current runtime."""
    current_version = (sys.version_info.major, sys.version_info.minor)
    candidate_commands = [
        "python3.14",
        "python3.13",
        "python3.12",
        "python3.11",
        "python3.10",
        "python3.9",
        "python3.8",
        "python3",
    ]
    seen: set[str] = set()
    for command in candidate_commands:
        interpreter_path = shutil.which(command)
        if not interpreter_path or interpreter_path in seen:
            continue
        seen.add(interpreter_path)
        probe = subprocess.run(
            [
                interpreter_path,
                "-c",
                "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')",
            ],
            capture_output=True,
            text=True,
        )
        if probe.returncode != 0:
            continue
        version_label = probe.stdout.strip()
        version_parts = version_label.split(".", 1)
        if len(version_parts) != 2:
            continue
        try:
            discovered_version = (int(version_parts[0]), int(version_parts[1]))
        except ValueError:
            continue
        if discovered_version < (3, 8):
            continue
        if discovered_version != current_version:
            return interpreter_path, discovered_version
    return None


def test_run_uses_runtime_path_python_override(tmp_path, capfd):
    alternate = _discover_alternate_python_interpreter()
    if alternate is None:
        pytest.skip("No alternate Python interpreter available for runtime.path override test")

    runtime_python, runtime_version = alternate
    agent_dir = tmp_path / "runtime-path-python-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text(
        "import sys\n"
        "print(f'RUNTIME_EXEC={sys.executable}')\n"
        "print(f'RUNTIME_VERSION={sys.version_info.major}.{sys.version_info.minor}')\n",
        encoding="utf-8",
    )
    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: runtime-path-python-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.8"
    type: one-shot
    path: "{runtime_python}"
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
        encoding="utf-8",
    )

    import kinnoo.run_command as run_command

    exit_code = run_command.run_agent(
        agent_dir_arg=str(agent_dir),
        input_arg="hello-runtime-path",
        no_guard=True,
    )

    output = capfd.readouterr()
    assert exit_code == 0, f"stdout={output.out!r} stderr={output.err!r}"

    runtime_exec_line = next(
        (line for line in output.out.splitlines() if line.startswith("RUNTIME_EXEC=")),
        None,
    )
    runtime_version_line = next(
        (line for line in output.out.splitlines() if line.startswith("RUNTIME_VERSION=")),
        None,
    )

    assert runtime_exec_line is not None
    assert runtime_version_line is not None

    runtime_exec = runtime_exec_line.split("=", 1)[1].strip()
    reported_version_label = runtime_version_line.split("=", 1)[1].strip()
    reported_version = tuple(int(part) for part in reported_version_label.split(".", 1))

    assert reported_version == runtime_version
    assert reported_version != (sys.version_info.major, sys.version_info.minor)
    assert runtime_exec == runtime_python
    assert not (agent_dir / ".venv").exists()


def test_run_uses_runtime_path_python_command_lookup(monkeypatch, tmp_path, capsys):
    agent_dir = tmp_path / "runtime-path-python-command-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text("print('runtime-path-python-command-test')\n", encoding="utf-8")

    fake_python = agent_dir / "fake-python"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_python.chmod(0o755)

    captured_calls: list[list[str]] = []

    class _FakePopen:
        def __init__(self, args, cwd=None, stdout=None, stderr=None, env=None):
            del cwd, stdout, stderr, env
            captured_calls.append(args)
            self.returncode = 0

        def communicate(self, timeout=None):
            del timeout
            return ("", "")

    import kinnoo.run_command as run_command

    monkeypatch.setattr(run_command.subprocess, "Popen", _FakePopen)

    def _fake_which(value: str):
        if value == "python3.12":
            return str(fake_python)
        return None

    monkeypatch.setattr(run_command.shutil, "which", _fake_which)

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: runtime-path-python-command-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.8"
    type: one-shot
    path: "python3.12"
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
        encoding="utf-8",
    )

    exit_code = run_command.run_agent(
        agent_dir_arg=str(agent_dir),
        input_arg="hello-runtime-path",
        no_guard=True,
    )

    output = capsys.readouterr()

    assert exit_code == 0
    assert captured_calls[0][0] == str(fake_python)
    assert "runtime.path is set but not an executable file" not in output.err
    assert not (agent_dir / ".venv").exists()


def test_run_runtime_path_python_installs_requirements(monkeypatch, tmp_path, capsys):
    agent_dir = tmp_path / "runtime-path-python-requirements-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("langchain-core\n", encoding="utf-8")
    (agent_dir / "run.py").write_text("print('runtime-path-python-reqs-test')\n", encoding="utf-8")

    fake_python = agent_dir / "fake-python"
    fake_python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_python.chmod(0o755)

    captured_run_calls: list[list[str]] = []
    captured_popen_calls: list[list[str]] = []

    class _Result:
        def __init__(self, code: int):
            self.returncode = code

    def _fake_run(args, stdout=None, stderr=None):
        del stdout, stderr
        captured_run_calls.append(args)
        if len(args) >= 4 and args[1] == "-m" and args[2] == "venv":
            venv_dir = Path(args[3])
            bin_dir = venv_dir / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            (bin_dir / "pip").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (bin_dir / "pip").chmod(0o755)
            (bin_dir / "python").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (bin_dir / "python").chmod(0o755)
            return _Result(0)
        if len(args) >= 2 and args[1] == "install":
            return _Result(0)
        return _Result(0)

    class _FakePopen:
        def __init__(self, args, cwd=None, stdout=None, stderr=None, env=None):
            del cwd, stdout, stderr, env
            captured_popen_calls.append(args)
            self.returncode = 0

        def communicate(self, timeout=None):
            del timeout
            return ("", "")

    import kinnoo.run_command as run_command

    monkeypatch.setattr(run_command.subprocess, "run", _fake_run)
    monkeypatch.setattr(run_command.subprocess, "Popen", _FakePopen)

    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: runtime-path-python-requirements-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.8"
    type: one-shot
    path: "{fake_python}"
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
        encoding="utf-8",
    )

    exit_code = run_command.run_agent(
        agent_dir_arg=str(agent_dir),
        input_arg="hello-runtime-path",
        no_guard=True,
    )

    output = capsys.readouterr()

    assert exit_code == 0
    assert any(call[:3] == [str(fake_python), "-m", "venv"] for call in captured_run_calls)
    assert any("pip" in call[0] and "install" in call for call in captured_run_calls)
    assert captured_popen_calls[0][0].endswith("/.venv/bin/python")
    assert "installing requirements for running agent" in output.out


def test_run_uses_runtime_path_node_override(monkeypatch, tmp_path, capsys):
    agent_dir = tmp_path / "runtime-path-node-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.js").write_text("console.log('runtime-path-node-test');\n", encoding="utf-8")

    fake_node = agent_dir / "fake-node"
    fake_node.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_node.chmod(0o755)

    captured_calls: list[list[str]] = []

    class _FakePopen:
        def __init__(self, args, cwd=None, stdout=None, stderr=None, env=None):
            del cwd, stdout, stderr, env
            captured_calls.append(args)
            self.returncode = 0

        def communicate(self, timeout=None):
            del timeout
            return ("", "")

    import kinnoo.run_command as run_command

    monkeypatch.setattr(run_command.subprocess, "Popen", _FakePopen)

    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: runtime-path-node-agent
version: 0.1.0
entrypoint: run.js
runtime:
    language: nodejs
    version: ">=18"
    type: one-shot
    path: "{fake_node}"
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
        encoding="utf-8",
    )

    valid_exit = run_command.run_agent(
        agent_dir_arg=str(agent_dir),
        input_arg="hello-node-runtime-path",
        no_guard=True,
    )

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: runtime-path-node-agent
version: 0.1.0
entrypoint: run.js
runtime:
    language: nodejs
    version: ">=18"
    type: one-shot
    path: "/definitely/missing/node"
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
        encoding="utf-8",
    )

    fallback_exit = run_command.run_agent(
        agent_dir_arg=str(agent_dir),
        input_arg="hello-node-runtime-path",
        no_guard=True,
    )

    output = capsys.readouterr()

    assert valid_exit == 0
    assert fallback_exit == 0
    assert captured_calls[0][0] == str(fake_node)
    assert captured_calls[1][0] == "node"
    assert "runtime.path is set but not an executable file and was not found on PATH" in output.err


def test_feature31_run_nodejs_entrypoint_streams_and_propagates_exit(monkeypatch, tmp_path, capsys):
    agent_dir = tmp_path / "feature31-node-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "run.js").write_text("console.log('placeholder');\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature31-node-agent
version: 0.1.0
entrypoint: run.js
runtime:
    language: nodejs
    version: ">=22"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
"""
    )

    captured: dict[str, object] = {}

    class _FakePopen:
        def __init__(self, args, cwd=None, stdout=None, stderr=None, env=None):
            captured["args"] = args
            captured["cwd"] = cwd
            captured["env"] = env
            self._stdout = stdout
            self._stderr = stderr
            self.returncode = 17

        def communicate(self):
            if self._stdout is not None:
                self._stdout.write("node-stdout-line\n")
                self._stdout.flush()
            if self._stderr is not None:
                self._stderr.write("node-stderr-line\n")
                self._stderr.flush()

    import kinnoo.run_command as run_command

    monkeypatch.setattr(run_command.subprocess, "Popen", _FakePopen)

    exit_code = run_command.run_agent(
        agent_dir_arg=str(agent_dir),
        input_arg="hello-node",
        no_guard=True,
        pass_through_args=["--flag", "value"],
    )

    output = capsys.readouterr()

    assert exit_code == 17
    assert captured["args"] == [
        "node",
        str(agent_dir / "run.js"),
        "hello-node",
        "--flag",
        "value",
    ]
    assert str(captured["cwd"]) == str(agent_dir.resolve())
    assert "node-stdout-line" in output.out
    assert "node-stderr-line" in output.err
    assert not (agent_dir / ".venv").exists()


def test_feature42_run_inline_json_input_mode(tmp_path):
    agent_dir = tmp_path / "feature42-json-inline-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature42-json-inline-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: json
outputs:
    type: text
"""
    )
    (agent_dir / "run.py").write_text(
        "import json\n"
        "import sys\n"
        "payload = json.loads(sys.argv[1])\n"
        "print(json.dumps(payload, sort_keys=True, separators=(',', ':')))\n"
    )
    (agent_dir / "README.md").write_text("feature42 inline json mode")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    inline_payload = '{"z":1,"a":{"k":"v"}}'
    result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "--json-input",
            inline_payload,
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert '{"a":{"k":"v"},"z":1}' in result.stdout


def test_feature42_run_json_file_input_mode(tmp_path):
    agent_dir = tmp_path / "feature42-json-file-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature42-json-file-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: json
outputs:
    type: text
"""
    )
    (agent_dir / "run.py").write_text(
        "import json\n"
        "import sys\n"
        "payload = json.loads(sys.argv[1])\n"
        "print('ok:' + payload['message'])\n"
    )
    (agent_dir / "README.md").write_text("feature42 json-file mode")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    valid_payload_file = tmp_path / "payload.json"
    valid_payload_file.write_text('{"message":"hello-from-file"}', encoding="utf-8")

    valid_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "--json-file",
            str(valid_payload_file),
        ],
        capture_output=True,
        text=True,
    )

    assert valid_result.returncode == 0, valid_result.stderr
    assert "ok:hello-from-file" in valid_result.stdout

    missing_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "--json-file",
            str(tmp_path / "missing.json"),
        ],
        capture_output=True,
        text=True,
    )

    assert missing_result.returncode != 0
    assert "JSON input file not found" in missing_result.stderr

    invalid_payload_file = tmp_path / "invalid_payload.json"
    invalid_payload_file.write_text('{"message":', encoding="utf-8")

    invalid_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "--json-file",
            str(invalid_payload_file),
        ],
        capture_output=True,
        text=True,
    )

    assert invalid_result.returncode != 0
    assert "Invalid JSON in --json-file payload" in invalid_result.stderr


def test_feature42_json_output_contract_enforcement(tmp_path):
    valid_agent = tmp_path / "feature42-json-output-valid-agent"
    valid_agent.mkdir()
    (valid_agent / "requirements.txt").write_text("")
    (valid_agent / "kinnoo.yaml").write_text(
        """
name: feature42-json-output-valid-agent
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
    type: json
"""
    )
    (valid_agent / "run.py").write_text(
        "import json\n"
        "print(json.dumps({'status': 'ok', 'value': 1}, sort_keys=True))\n"
    )
    (valid_agent / "README.md").write_text("feature42 valid json output")
    (valid_agent / "tools").mkdir()
    (valid_agent / "prompts").mkdir()

    valid_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(valid_agent), "hello"],
        capture_output=True,
        text=True,
    )

    assert valid_result.returncode == 0, valid_result.stderr
    assert '{"status": "ok", "value": 1}' in valid_result.stdout

    invalid_agent = tmp_path / "feature42-json-output-invalid-agent"
    invalid_agent.mkdir()
    (invalid_agent / "requirements.txt").write_text("")
    (invalid_agent / "kinnoo.yaml").write_text(
        """
name: feature42-json-output-invalid-agent
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
    type: json
"""
    )
    (invalid_agent / "run.py").write_text(
        "print('not-json-output')\n"
    )
    (invalid_agent / "README.md").write_text("feature42 invalid json output")
    (invalid_agent / "tools").mkdir()
    (invalid_agent / "prompts").mkdir()

    secret_input = "TOP_SECRET_TOKEN_123"
    invalid_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(invalid_agent), secret_input],
        capture_output=True,
        text=True,
    )

    assert invalid_result.returncode != 0
    assert "outputs.type=json contract violation" in invalid_result.stderr
    assert "line" in invalid_result.stderr and "column" in invalid_result.stderr
    assert secret_input not in invalid_result.stderr


@pytest.mark.parametrize(
    ("runtime_language", "entrypoint_name", "entrypoint_contents"),
    [
        (
            "python",
            "run.py",
            "import time\nwhile True:\n    time.sleep(60)\n",
        ),
        (
            "nodejs",
            "run.js",
            "setInterval(() => {}, 60000);\n",
        ),
    ],
)
def test_feature32_run_daemon_start_persists_state(
    monkeypatch,
    tmp_path,
    capsys,
    runtime_language,
    entrypoint_name,
    entrypoint_contents,
):
    agent_dir = tmp_path / f"feature32-daemon-{runtime_language}-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("")
    (agent_dir / entrypoint_name).write_text(entrypoint_contents, encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                f"name: feature32-daemon-{runtime_language}-agent",
                "version: 0.1.0",
                f"entrypoint: {entrypoint_name}",
                "runtime:",
                f"    language: {runtime_language}",
                "    version: \">=3.10\"" if runtime_language == "python" else "    version: \">=22\"",
                "    type: daemon",
                "dependencies: []",
                "inputs:",
                "    type: text",
                "outputs:",
                "    type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    if runtime_language == "python":
        # Pre-create minimal venv layout so test does not invoke real venv.create,
        # which internally uses subprocess.Popen with additional kwargs.
        venv_python = agent_dir / ".venv" / "bin" / "python"
        venv_python.parent.mkdir(parents=True, exist_ok=True)
        venv_python.write_text("", encoding="utf-8")

    class _FakeDaemonPopen:
        def __init__(self, args, cwd=None, stdout=None, stderr=None, env=None, start_new_session=False):
            self.args = args
            self.cwd = cwd
            self.stdout = stdout
            self.stderr = stderr
            self.env = env
            self.start_new_session = start_new_session
            self.pid = 54321 if runtime_language == "python" else 65432

    import kinnoo.run_command as run_command

    monkeypatch.setattr(run_command.subprocess, "Popen", _FakeDaemonPopen)

    exit_code = run_command.run_agent(
        agent_dir_arg=str(agent_dir),
        input_arg="hello-daemon",
        no_guard=True,
    )

    captured = capsys.readouterr()
    combined_output = f"{captured.out}\n{captured.err}"

    assert exit_code == 0, combined_output
    assert "daemon started" in combined_output
    assert "control hints" in combined_output

    state_path = agent_dir / ".kinnoo" / "daemon-state.json"
    log_path = agent_dir / ".kinnoo" / "daemon.log"
    assert state_path.exists(), "Expected daemon state file to be persisted"
    assert log_path.exists(), "Expected daemon log file to be created"

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["runtime_type"] == "daemon"
    assert state["runtime_language"] == runtime_language
    assert state["agent_dir"] == str(agent_dir.resolve())
    assert state["entrypoint"] == entrypoint_name
    assert state["pid"] in (54321, 65432)
    assert state["state_version"] == 1
    assert state["command"][0] == ("node" if runtime_language == "nodejs" else str(agent_dir / ".venv" / "bin" / "python"))


def test_feature32_stop_daemon_graceful_and_fallback(monkeypatch, tmp_path, capsys):
    import kinnoo.run_command as run_command
    from kinnoo.supervisor import DaemonStopReport

    graceful_agent = tmp_path / "feature32-stop-graceful-agent"
    graceful_agent.mkdir()
    graceful_state = graceful_agent / ".kinnoo" / "daemon-state.json"
    graceful_state.parent.mkdir(parents=True, exist_ok=True)
    graceful_state.write_text(
        json.dumps(
            {
                "pid": 42001,
                "runtime_type": "daemon",
                "runtime_language": "python",
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    fallback_agent = tmp_path / "feature32-stop-fallback-agent"
    fallback_agent.mkdir()
    fallback_state = fallback_agent / ".kinnoo" / "daemon-state.json"
    fallback_state.parent.mkdir(parents=True, exist_ok=True)
    fallback_state.write_text(
        json.dumps(
            {
                "pid": 42002,
                "runtime_type": "daemon",
                "runtime_language": "nodejs",
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    observed_pids: list[int] = []

    def fake_stop_daemon_pid(pid: int, timeout_seconds: float = 3.0, poll_interval_seconds: float = 0.05):
        del timeout_seconds, poll_interval_seconds
        observed_pids.append(pid)
        if pid == 42001:
            return DaemonStopReport(
                pid=pid,
                terminated=True,
                already_stopped=False,
                sigterm_sent=True,
                sigkill_sent=False,
            )
        return DaemonStopReport(
            pid=pid,
            terminated=True,
            already_stopped=False,
            sigterm_sent=True,
            sigkill_sent=True,
        )

    monkeypatch.setattr(run_command, "stop_daemon_pid", fake_stop_daemon_pid)

    graceful_exit_code = run_command.stop_agent(str(graceful_agent))
    fallback_exit_code = run_command.stop_agent(str(fallback_agent))

    captured = capsys.readouterr()
    combined_output = f"{captured.out}\n{captured.err}"

    assert graceful_exit_code == 0, combined_output
    assert fallback_exit_code == 0, combined_output
    assert observed_pids == [42001, 42002]
    assert "daemon stopped gracefully with SIGTERM: pid=42001" in combined_output
    assert "daemon stopped with fallback SIGKILL: pid=42002" in combined_output
    assert "daemon state metadata cleared" in combined_output
    assert not graceful_state.exists(), "Expected graceful stop to clear daemon-state metadata"
    assert not fallback_state.exists(), "Expected fallback stop to clear daemon-state metadata"


def test_feature32_attach_daemon_session_controls(monkeypatch, tmp_path, capsys):
    import kinnoo.run_command as run_command

    supported_agent = tmp_path / "feature32-attach-supported-agent"
    supported_agent.mkdir()
    supported_log = supported_agent / ".kinnoo" / "daemon.log"
    supported_log.parent.mkdir(parents=True, exist_ok=True)
    supported_log.write_text("daemon output line\n", encoding="utf-8")
    (supported_agent / ".kinnoo" / "daemon-state.json").write_text(
        json.dumps(
            {
                "pid": 43001,
                "runtime_type": "daemon",
                "runtime_language": "python",
                "log_path": str(supported_log),
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    non_running_agent = tmp_path / "feature32-attach-non-running-agent"
    non_running_agent.mkdir()
    (non_running_agent / ".kinnoo").mkdir(parents=True, exist_ok=True)
    (non_running_agent / ".kinnoo" / "daemon-state.json").write_text(
        json.dumps(
            {
                "pid": 43002,
                "runtime_type": "daemon",
                "runtime_language": "nodejs",
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    unsupported_mode_agent = tmp_path / "feature32-attach-unsupported-agent"
    unsupported_mode_agent.mkdir()
    (unsupported_mode_agent / ".kinnoo").mkdir(parents=True, exist_ok=True)
    (unsupported_mode_agent / ".kinnoo" / "daemon-state.json").write_text(
        json.dumps(
            {
                "pid": 43003,
                "runtime_type": "one-shot",
                "runtime_language": "python",
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    non_tty_agent = tmp_path / "feature32-attach-non-tty-agent"
    non_tty_agent.mkdir()
    non_tty_log = non_tty_agent / ".kinnoo" / "daemon.log"
    non_tty_log.parent.mkdir(parents=True, exist_ok=True)
    non_tty_log.write_text("", encoding="utf-8")
    (non_tty_agent / ".kinnoo" / "daemon-state.json").write_text(
        json.dumps(
            {
                "pid": 43004,
                "runtime_type": "daemon",
                "runtime_language": "python",
                "log_path": str(non_tty_log),
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    pid_status_calls = {"supported": 0}

    def fake_pid_running(pid: int) -> bool:
        if pid == 43001:
            pid_status_calls["supported"] += 1
            # First check confirms running; second check ends attach loop deterministically.
            return pid_status_calls["supported"] == 1
        if pid == 43002:
            return False
        if pid == 43004:
            return True
        return True

    monkeypatch.setattr(run_command, "daemon_pid_is_running", fake_pid_running)

    monkeypatch.setattr(run_command.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(run_command.sys.stdout, "isatty", lambda: True)
    supported_exit = run_command.attach_agent(str(supported_agent))

    non_running_exit = run_command.attach_agent(str(non_running_agent))
    unsupported_mode_exit = run_command.attach_agent(str(unsupported_mode_agent))

    monkeypatch.setattr(run_command.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(run_command.sys.stdout, "isatty", lambda: True)
    non_tty_exit = run_command.attach_agent(str(non_tty_agent))

    captured = capsys.readouterr()
    combined_output = f"{captured.out}\n{captured.err}"

    assert supported_exit == 0, combined_output
    assert non_running_exit == 1, combined_output
    assert unsupported_mode_exit == 1, combined_output
    assert non_tty_exit == 1, combined_output
    assert "attach session started" in combined_output
    assert "daemon output line" in combined_output
    assert "daemon exited; attach session ending" in combined_output
    assert "daemon is not running" in combined_output
    assert "attach is unsupported for runtime.type" in combined_output
    assert "attach requires an interactive TTY session" in combined_output


def test_feature32_logs_daemon_tail_and_follow(monkeypatch, tmp_path, capsys):
    import kinnoo.run_command as run_command

    tail_agent = tmp_path / "feature32-logs-tail-agent"
    tail_agent.mkdir()
    tail_log = tail_agent / ".kinnoo" / "daemon.log"
    tail_log.parent.mkdir(parents=True, exist_ok=True)
    tail_log.write_text("line-1\nline-2\nline-3\n", encoding="utf-8")
    (tail_agent / ".kinnoo" / "daemon-state.json").write_text(
        json.dumps(
            {
                "pid": 44001,
                "runtime_type": "daemon",
                "runtime_language": "python",
                "log_path": str(tail_log),
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    follow_agent = tmp_path / "feature32-logs-follow-agent"
    follow_agent.mkdir()
    follow_log = follow_agent / ".kinnoo" / "daemon.log"
    follow_log.parent.mkdir(parents=True, exist_ok=True)
    follow_log.write_text("startup-line\n", encoding="utf-8")
    (follow_agent / ".kinnoo" / "daemon-state.json").write_text(
        json.dumps(
            {
                "pid": 44002,
                "runtime_type": "daemon",
                "runtime_language": "nodejs",
                "log_path": str(follow_log),
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    missing_log_agent = tmp_path / "feature32-logs-missing-log-agent"
    missing_log_agent.mkdir()
    missing_log_path = missing_log_agent / ".kinnoo" / "daemon.log"
    missing_log_path.parent.mkdir(parents=True, exist_ok=True)
    (missing_log_agent / ".kinnoo" / "daemon-state.json").write_text(
        json.dumps(
            {
                "pid": 44003,
                "runtime_type": "daemon",
                "runtime_language": "python",
                "log_path": str(missing_log_path),
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    non_running_follow_agent = tmp_path / "feature32-logs-non-running-agent"
    non_running_follow_agent.mkdir()
    non_running_log = non_running_follow_agent / ".kinnoo" / "daemon.log"
    non_running_log.parent.mkdir(parents=True, exist_ok=True)
    non_running_log.write_text("last-known\n", encoding="utf-8")
    (non_running_follow_agent / ".kinnoo" / "daemon-state.json").write_text(
        json.dumps(
            {
                "pid": 44004,
                "runtime_type": "daemon",
                "runtime_language": "python",
                "log_path": str(non_running_log),
                "state_version": 1,
            }
        ),
        encoding="utf-8",
    )

    pid_calls = {"follow": 0}
    appended_follow_line = {"done": False}

    def fake_pid_running(pid: int) -> bool:
        if pid == 44001:
            return True
        if pid == 44002:
            pid_calls["follow"] += 1
            return pid_calls["follow"] <= 2
        if pid == 44003:
            return True
        if pid == 44004:
            return False
        return False

    def fake_sleep(_seconds: float) -> None:
        if not appended_follow_line["done"]:
            with follow_log.open("a", encoding="utf-8") as handle:
                handle.write("follow-line\n")
            appended_follow_line["done"] = True

    monkeypatch.setattr(run_command, "daemon_pid_is_running", fake_pid_running)
    monkeypatch.setattr(run_command.time, "sleep", fake_sleep)

    tail_exit = run_command.logs_agent(str(tail_agent), follow=False, tail_lines=2)
    follow_exit = run_command.logs_agent(str(follow_agent), follow=True, tail_lines=1)
    missing_log_exit = run_command.logs_agent(str(missing_log_agent), follow=False, tail_lines=5)
    non_running_follow_exit = run_command.logs_agent(
        str(non_running_follow_agent),
        follow=True,
        tail_lines=5,
    )

    captured = capsys.readouterr()
    combined_output = f"{captured.out}\n{captured.err}"

    assert tail_exit == 0, combined_output
    assert follow_exit == 0, combined_output
    assert missing_log_exit == 1, combined_output
    assert non_running_follow_exit == 1, combined_output
    assert "[daemon.log] line-2" in combined_output
    assert "[daemon.log] line-3" in combined_output
    assert "[daemon.log] startup-line" in combined_output
    assert "[daemon.log] follow-line" in combined_output
    assert "daemon exited; follow mode ended" in combined_output
    assert "daemon log file not found" in combined_output
    assert "follow mode requires an active daemon" in combined_output


def test_feature34_openclaw_template_smoke_run(tmp_path):
    """test289: generated OpenClaw scaffold runs via kinnoo run with required env vars configured."""
    agent_name = "feature34-openclaw-smoke"
    cli_script = str((Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"))

    init_result = subprocess.run(
        [sys.executable, cli_script, "init", agent_name, "--framework", "openclaw"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert init_result.returncode == 0, init_result.stderr

    agent_dir = tmp_path / agent_name
    env = os.environ.copy()
    env["OPENCLAW_API_KEY"] = "test-openclaw-api-key"
    env["KINNOO_TEST_SAFE_MODE"] = "1"

    state_path = agent_dir / ".kinnoo" / "daemon-state.json"
    run_result = subprocess.run(
        [
            sys.executable,
            cli_script,
            "run",
            str(agent_dir),
            "smoke-input",
            "--no-guard",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    try:
        run_output = f"{run_result.stdout}\n{run_result.stderr}"
        assert run_result.returncode == 0, run_output
        assert run_output.strip(), "Expected deterministic non-empty run output"
        assert "[kinnoo] daemon started:" in run_output
        assert "control hints" in run_output

        log_path = agent_dir / ".kinnoo" / "daemon.log"
        assert state_path.exists(), "Expected daemon state metadata after run"
        assert log_path.exists(), "Expected daemon log file after run"

        stop_result = subprocess.run(
            [sys.executable, cli_script, "stop", str(agent_dir)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            env=env,
        )
        stop_output = f"{stop_result.stdout}\n{stop_result.stderr}"
        assert stop_result.returncode == 0, stop_output
        assert "daemon stopped" in stop_output or "daemon already not running" in stop_output
        assert not state_path.exists(), "Expected daemon state metadata to be cleared after stop"
    finally:
        if state_path.exists():
            subprocess.run(
                [sys.executable, cli_script, "stop", str(agent_dir)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                env=env,
            )


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


def test_feature25_run_checks_all_declared_services_before_entrypoint(tmp_path):
    import socket
    import subprocess
    import time
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            del format, args

    http_server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
    http_host, http_port = http_server.server_address
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(("127.0.0.1", 0))
    tcp_socket.listen(1)
    tcp_port = tcp_socket.getsockname()[1]
    stop_accept = threading.Event()

    def _accept_loop() -> None:
        while not stop_accept.is_set():
            try:
                tcp_socket.settimeout(0.1)
                conn, _ = tcp_socket.accept()
                conn.close()
            except TimeoutError:
                continue
            except OSError:
                break

    tcp_thread = threading.Thread(target=_accept_loop, daemon=True)
    tcp_thread.start()

    agent_dir = tmp_path / "feature25-run-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "README.md").write_text("feature25 run fixture", encoding="utf-8")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    (agent_dir / "run.py").write_text(
        "print('feature25-entrypoint-ran')\n",
        encoding="utf-8",
    )
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature25-run-agent",
                "version: 0.1.0",
                "entrypoint: run.py",
                "runtime:",
                "    language: python",
                "    version: \">=3.10\"",
                "    type: one-shot",
                "dependencies: []",
                "inputs:",
                "    type: text",
                "outputs:",
                "    type: text",
                "services:",
                "  - name: local-api",
                "    type: api",
                "    health_check:",
                "      method: http",
                f"      url: http://{http_host}:{http_port}/health",
                "  - name: local-db",
                "    type: database",
                "    health_check:",
                "      method: tcp",
                f"      port: {tcp_port}",
                "  - name: local-redis",
                "    type: local-process",
                "    health_check:",
                "      method: process",
                "      process_name: feature25-running-process",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cli_path = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    fixture_process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(20)",
            "feature25-running-process",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        time.sleep(0.2)
        result = subprocess.run(
            [sys.executable, str(cli_path), "run", str(agent_dir), "hello"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0
        assert "[kinnoo] Service health checks:" in output
        assert "service 'local-api'" in output
        assert "service 'local-db'" in output
        assert "service 'local-redis'" in output
        assert "(type: local-process, method: process)" in output
        assert "[kinnoo] service check [PASS]" in output
        assert "feature25-entrypoint-ran" in output

        if (
            "[kinnoo] Service health checks:" in result.stdout
            and "feature25-entrypoint-ran" in result.stdout
        ):
            health_section_index = result.stdout.index("[kinnoo] Service health checks:")
            entrypoint_index = result.stdout.index("feature25-entrypoint-ran")
            assert health_section_index < entrypoint_index
    finally:
        fixture_process.terminate()
        fixture_process.wait(timeout=5)
        stop_accept.set()
        tcp_socket.close()
        http_server.shutdown()
        http_server.server_close()


def _write_feature25_service_policy_agent(tmp_path: Path, *, process_name: str) -> Path:
    agent_dir = tmp_path / "feature25-policy-agent"
    agent_dir.mkdir()
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "README.md").write_text("feature25 policy fixture", encoding="utf-8")
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()
    (agent_dir / "run.py").write_text(
        "print('feature25-policy-entrypoint-ran')\n",
        encoding="utf-8",
    )
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature25-policy-agent",
                "version: 0.1.0",
                "entrypoint: run.py",
                "runtime:",
                "    language: python",
                "    version: \">=3.10\"",
                "    type: one-shot",
                "dependencies: []",
                "inputs:",
                "    type: text",
                "outputs:",
                "    type: text",
                "services:",
                "  - name: local-redis",
                "    type: local-process",
                "    health_check:",
                "      method: process",
                f"      process_name: {process_name}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    venv_python = agent_dir / ".venv" / "bin" / "python"
    venv_python.parent.mkdir(parents=True, exist_ok=True)
    venv_python.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    venv_python.chmod(0o755)

    return agent_dir


def test_feature25_non_interactive_aborts_on_unhealthy_service(tmp_path, monkeypatch, capsys):
    from kinnoo import run_command

    agent_dir = _write_feature25_service_policy_agent(
        tmp_path,
        process_name="feature25-missing-process-non-interactive",
    )

    monkeypatch.setattr(run_command.sys.stdin, "isatty", lambda: False)
    exit_code = run_command.run_agent(str(agent_dir), "hello")

    captured = capsys.readouterr()
    output = f"{captured.out}\n{captured.err}"
    assert exit_code != 0
    assert "service 'local-redis'" in output
    assert "Non-interactive mode: aborting due to unhealthy service check." in output
    assert "feature25-policy-entrypoint-ran" not in output


def test_feature25_interactive_prompt_allows_proceed_or_abort(tmp_path, monkeypatch, capsys):
    import builtins

    from kinnoo.health_check import HealthCheckResult
    from kinnoo import run_command

    agent_dir = _write_feature25_service_policy_agent(
        tmp_path,
        process_name="feature25-missing-process-interactive",
    )

    monkeypatch.setattr(run_command.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(
        run_command,
        "_run_service_checks",
        lambda _manifest: [
            HealthCheckResult(
                service_name="local-redis",
                service_type="local-process",
                method="process",
                healthy=False,
                message="Process health check failed for pattern 'feature25-missing-process-interactive'.",
                guidance=(
                    "Start the required process, or update services[].health_check.process_name "
                    "to match the running command."
                ),
            )
        ],
    )

    prompts: list[str] = []

    def _proceed_prompt(message: str) -> str:
        prompts.append(message)
        return "y"

    popen_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    class _FakeProcess:
        def __init__(self) -> None:
            self.returncode = 0

        def communicate(self) -> None:
            print("feature25-policy-entrypoint-ran")

    def _fake_popen(*args: object, **kwargs: object) -> _FakeProcess:
        popen_calls.append((args, kwargs))
        return _FakeProcess()

    monkeypatch.setattr(run_command.subprocess, "Popen", _fake_popen)
    monkeypatch.setattr(builtins, "input", _proceed_prompt)
    proceed_code = run_command.run_agent(str(agent_dir), "hello")
    proceed_captured = capsys.readouterr()
    proceed_output = f"{proceed_captured.out}\n{proceed_captured.err}"

    assert proceed_code == 0, proceed_output
    assert prompts, "Expected an interactive unhealthy-service prompt"
    assert prompts[0] == "Service local-redis is not healthy. Proceed anyway? [y/N] "
    assert "feature25-policy-entrypoint-ran" in proceed_output
    assert popen_calls, "Expected entrypoint launch when interactive user proceeds"

    def _abort_prompt(_message: str) -> str:
        return ""

    monkeypatch.setattr(builtins, "input", _abort_prompt)
    abort_code = run_command.run_agent(str(agent_dir), "hello")
    abort_captured = capsys.readouterr()
    abort_output = f"{abort_captured.out}\n{abort_captured.err}"

    assert abort_code != 0
    assert "feature25-policy-entrypoint-ran" not in abort_output


def test_feature39_run_sandbox_permission_enforcement(tmp_path):
    allowed_agent_dir = tmp_path / "feature39-sandbox-allowed-agent"
    allowed_agent_dir.mkdir()
    (allowed_agent_dir / "requirements.txt").write_text("")
    (allowed_agent_dir / "kinnoo.yaml").write_text(
        """
name: feature39-sandbox-allowed-agent
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
permissions:
    network: true
    filesystem_scope: read-only
    shell: false
    browser: false
    env_access: []
"""
    )
    (allowed_agent_dir / "run.py").write_text("print('feature39-sandbox-allowed-ran')\n")
    (allowed_agent_dir / "README.md").write_text("feature39 sandbox allowed agent")
    (allowed_agent_dir / "tools").mkdir()
    (allowed_agent_dir / "prompts").mkdir()

    allowed_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(allowed_agent_dir),
            "hello",
            "--sandbox",
            "--",
            "--url",
            "https://example.com",
        ],
        capture_output=True,
        text=True,
    )

    allowed_output = f"{allowed_result.stdout}\n{allowed_result.stderr}"
    assert allowed_result.returncode == 0, allowed_output
    assert "sandbox policy check passed" in allowed_output
    assert "feature39-sandbox-allowed-ran" in allowed_output

    denied_agent_dir = tmp_path / "feature39-sandbox-denied-agent"
    denied_agent_dir.mkdir()
    (denied_agent_dir / "requirements.txt").write_text("")
    (denied_agent_dir / "kinnoo.yaml").write_text(
        """
name: feature39-sandbox-denied-agent
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
permissions:
    network: true
    filesystem_scope: read-only
    shell: false
    browser: false
    env_access: []
"""
    )
    (denied_agent_dir / "run.py").write_text("print('feature39-sandbox-denied-should-not-run')\n")
    (denied_agent_dir / "README.md").write_text("feature39 sandbox denied agent")
    (denied_agent_dir / "tools").mkdir()
    (denied_agent_dir / "prompts").mkdir()

    denied_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(denied_agent_dir),
            "hello",
            "--sandbox",
            "--",
            "--exec",
            "echo denied",
        ],
        capture_output=True,
        text=True,
    )

    denied_output = f"{denied_result.stdout}\n{denied_result.stderr}"
    assert denied_result.returncode != 0, denied_output
    assert "classification=policy_violation" in denied_output
    assert "capability=shell action=shell_execution" in denied_output
    assert "Remediation:" in denied_output
    assert "feature39-sandbox-denied-should-not-run" not in denied_output


def test_feature39_sandbox_backend_failure_shapes() -> None:
    from kinnoo.sandbox import evaluate_sandbox_permissions

    base_manifest = {
        "permissions": {
            "network": True,
            "filesystem_scope": "read-only",
            "shell": False,
            "browser": False,
            "env_access": [],
        }
    }

    unsupported_runtime = evaluate_sandbox_permissions(
        manifest=base_manifest,
        runtime_type="daemon",
        runtime_language="python",
        pass_through_args=["--exec", "echo denied"],
    )
    assert unsupported_runtime.allowed is False
    assert unsupported_runtime.code == "backend_unsupported_runtime"
    assert "runtime.type='one-shot'" in unsupported_runtime.message
    assert "run without --sandbox" in unsupported_runtime.remediation

    unsupported_runtime_language = evaluate_sandbox_permissions(
        manifest=base_manifest,
        runtime_type="one-shot",
        runtime_language="ruby",
        pass_through_args=["--exec", "echo denied"],
    )
    assert unsupported_runtime_language.allowed is False
    assert unsupported_runtime_language.code == "backend_unsupported_runtime_language"
    assert "runtime.language='python' and 'nodejs'" in unsupported_runtime_language.message
    assert "run without --sandbox" in unsupported_runtime_language.remediation

    missing_permissions = evaluate_sandbox_permissions(
        manifest={},
        runtime_type="one-shot",
        runtime_language="python",
        pass_through_args=["--exec", "echo denied"],
    )
    assert missing_permissions.allowed is False
    assert missing_permissions.code == "missing_permissions_policy"
    assert "requires manifest permissions declaration" in missing_permissions.message
    assert "Declare a permissions section" in missing_permissions.remediation


def test_feature41_violation_enforcement_and_kill_switch(tmp_path):
    warn_agent_dir = tmp_path / "feature41-warn-agent"
    warn_agent_dir.mkdir()
    (warn_agent_dir / "requirements.txt").write_text("")
    (warn_agent_dir / "kinnoo.yaml").write_text(
        """
name: feature41-warn-agent
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
permissions:
    network: false
    filesystem_scope: read-only
    shell: false
    browser: false
    env_access: []
"""
    )
    (warn_agent_dir / "run.py").write_text("print('feature41-warn-agent-ran')\n")
    (warn_agent_dir / "README.md").write_text("feature41 warn agent")
    (warn_agent_dir / "tools").mkdir()
    (warn_agent_dir / "prompts").mkdir()

    warn_env = dict(os.environ)
    warn_env["KINNOO_MONITOR_ENFORCEMENT_MODE"] = "warn"
    warn_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(warn_agent_dir),
            "hello",
            "--sandbox",
            "--",
            "--url",
            "https://example.com",
        ],
        capture_output=True,
        text=True,
        env=warn_env,
    )

    warn_output = f"{warn_result.stdout}\n{warn_result.stderr}"
    assert warn_result.returncode == 0, warn_output
    assert "reason_code=soft_policy_warning" in warn_output
    assert "sandbox policy warning recorded" in warn_output
    assert "feature41-warn-agent-ran" in warn_output

    warn_events_path = warn_agent_dir / ".kinnoo" / "violation-events.jsonl"
    assert warn_events_path.exists(), warn_output
    warn_lines = [line for line in warn_events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert warn_lines
    warn_payload = json.loads(warn_lines[-1])
    assert warn_payload["enforcement_action"] == "warn_continue"
    assert warn_payload["reason_code"] == "soft_policy_warning"

    kill_agent_dir = tmp_path / "feature41-kill-agent"
    kill_agent_dir.mkdir()
    (kill_agent_dir / "requirements.txt").write_text("")
    (kill_agent_dir / "kinnoo.yaml").write_text(
        """
name: feature41-kill-agent
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
permissions:
    network: true
    filesystem_scope: read-only
    shell: false
    browser: false
    env_access: []
"""
    )
    (kill_agent_dir / "run.py").write_text("print('feature41-kill-agent-should-not-run')\n")
    (kill_agent_dir / "README.md").write_text("feature41 kill agent")
    (kill_agent_dir / "tools").mkdir()
    (kill_agent_dir / "prompts").mkdir()

    kill_env = dict(os.environ)
    kill_env["KINNOO_MONITOR_ENFORCEMENT_MODE"] = "warn"
    kill_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(kill_agent_dir),
            "hello",
            "--sandbox",
            "--",
            "--exec",
            "echo denied",
        ],
        capture_output=True,
        text=True,
        env=kill_env,
    )

    kill_output = f"{kill_result.stdout}\n{kill_result.stderr}"
    assert kill_result.returncode != 0, kill_output
    assert "reason_code=hard_shell_execution_violation" in kill_output
    assert "kill switch activated" in kill_output
    assert "feature41-kill-agent-should-not-run" not in kill_output

    kill_events_path = kill_agent_dir / ".kinnoo" / "violation-events.jsonl"
    assert kill_events_path.exists(), kill_output
    kill_lines = [line for line in kill_events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert kill_lines
    kill_payload = json.loads(kill_lines[-1])
    assert kill_payload["enforcement_action"] == "kill_switch_terminate"
    assert kill_payload["reason_code"] == "hard_shell_execution_violation"


def test_feature41_resource_control_enforcement(tmp_path):
    timeout_agent_dir = tmp_path / "feature41-timeout-agent"
    timeout_agent_dir.mkdir()
    (timeout_agent_dir / "requirements.txt").write_text("")
    (timeout_agent_dir / "kinnoo.yaml").write_text(
        """
name: feature41-timeout-agent
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
    (timeout_agent_dir / "run.py").write_text(
        "import time\n"
        "time.sleep(3)\n"
        "print('timeout-agent-ran')\n"
    )
    (timeout_agent_dir / "README.md").write_text("feature41 timeout agent")
    (timeout_agent_dir / "tools").mkdir()
    (timeout_agent_dir / "prompts").mkdir()

    timeout_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(timeout_agent_dir),
            "hello",
            "--max-seconds",
            "0.2",
        ],
        capture_output=True,
        text=True,
    )
    timeout_output = f"{timeout_result.stdout}\n{timeout_result.stderr}"
    assert timeout_result.returncode != 0, timeout_output
    assert "reason_code=wall_clock_timeout_exceeded" in timeout_output

    if os.name == "posix":
        cpu_agent_dir = tmp_path / "feature41-cpu-agent"
        cpu_agent_dir.mkdir()
        (cpu_agent_dir / "requirements.txt").write_text("")
        (cpu_agent_dir / "kinnoo.yaml").write_text(
            """
name: feature41-cpu-agent
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
        (cpu_agent_dir / "run.py").write_text(
            "while True:\n"
            "    pass\n"
        )
        (cpu_agent_dir / "README.md").write_text("feature41 cpu agent")
        (cpu_agent_dir / "tools").mkdir()
        (cpu_agent_dir / "prompts").mkdir()

        cpu_result = subprocess.run(
            [
                sys.executable,
                "src/kinnoo/cli.py",
                "run",
                str(cpu_agent_dir),
                "hello",
                "--max-cpu-seconds",
                "1",
                "--max-seconds",
                "3",
            ],
            capture_output=True,
            text=True,
        )
        cpu_output = f"{cpu_result.stdout}\n{cpu_result.stderr}"
        assert cpu_result.returncode != 0, cpu_output
        assert (
            "reason_code=cpu_limit_exceeded" in cpu_output
            or "reason_code=wall_clock_timeout_exceeded" in cpu_output
        )

    degraded_agent_dir = tmp_path / "feature41-degraded-agent"
    degraded_agent_dir.mkdir()
    (degraded_agent_dir / "requirements.txt").write_text("")
    (degraded_agent_dir / "kinnoo.yaml").write_text(
        """
name: feature41-degraded-agent
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
    (degraded_agent_dir / "run.py").write_text("print('feature41-degraded-agent-ran')\n")
    (degraded_agent_dir / "README.md").write_text("feature41 degraded agent")
    (degraded_agent_dir / "tools").mkdir()
    (degraded_agent_dir / "prompts").mkdir()

    degraded_env = dict(os.environ)
    degraded_env["KINNOO_FORCE_RESOURCE_LIMIT_UNSUPPORTED"] = "1"
    degraded_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(degraded_agent_dir),
            "hello",
            "--max-cpu-seconds",
            "1",
            "--max-memory-mb",
            "64",
        ],
        capture_output=True,
        text=True,
        env=degraded_env,
    )
    degraded_output = f"{degraded_result.stdout}\n{degraded_result.stderr}"
    assert degraded_result.returncode == 0, degraded_output
    assert "max-cpu-seconds unsupported on this platform; running in degraded mode" in degraded_output
    assert "max-memory-mb unsupported on this platform; running in degraded mode" in degraded_output
    assert "feature41-degraded-agent-ran" in degraded_output


def test_feature41_dry_run_monitoring_trace(tmp_path):
    dry_run_agent_dir = tmp_path / "feature41-dry-run-agent"
    dry_run_agent_dir.mkdir()
    (dry_run_agent_dir / "requirements.txt").write_text("")
    (dry_run_agent_dir / "kinnoo.yaml").write_text(
        """
name: feature41-dry-run-agent
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
    (dry_run_agent_dir / "run.py").write_text(
        "from pathlib import Path\n"
        "import socket\n"
        "Path('feature41-dry-run-side-effect.flag').write_text('executed', encoding='utf-8')\n"
        "socket.create_connection(('127.0.0.1', 9), timeout=0.1)\n"
        "print('feature41-dry-run-entrypoint-ran')\n"
    )
    (dry_run_agent_dir / "README.md").write_text("feature41 dry-run agent")
    (dry_run_agent_dir / "tools").mkdir()
    (dry_run_agent_dir / "prompts").mkdir()

    dry_run_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(dry_run_agent_dir),
            "hello",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    dry_run_output = f"{dry_run_result.stdout}\n{dry_run_result.stderr}"
    assert dry_run_result.returncode == 0, dry_run_output
    assert "dry-run mode enabled: entrypoint execution suppressed" in dry_run_output
    assert "dry-run predicted actions:" in dry_run_output
    assert "process::process_spawn" in dry_run_output
    assert "network::network_access_attempt" in dry_run_output
    assert "filesystem::filesystem_write" in dry_run_output

    side_effect_flag = dry_run_agent_dir / "feature41-dry-run-side-effect.flag"
    assert not side_effect_flag.exists()
    assert "feature41-dry-run-entrypoint-ran" not in dry_run_output


def test_feature40_keygen_generates_ed25519_keypair(tmp_path):
    from kinnoo.signing import (
        load_ed25519_private_key,
        load_ed25519_public_key,
        sign_payload,
        verify_signature,
    )

    private_key_path = tmp_path / "feature40-private.pem"
    public_key_path = tmp_path / "feature40-public.pem"

    result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "keygen",
            "--private-key",
            str(private_key_path),
            "--public-key",
            str(public_key_path),
        ],
        capture_output=True,
        text=True,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined_output
    assert private_key_path.exists()
    assert public_key_path.exists()

    private_key_pem = private_key_path.read_text(encoding="utf-8")
    public_key_pem = public_key_path.read_text(encoding="utf-8")
    assert "BEGIN PRIVATE KEY" in private_key_pem
    assert "BEGIN PUBLIC KEY" in public_key_pem

    if os.name != "nt":
        import stat

        private_mode = stat.S_IMODE(private_key_path.stat().st_mode)
        public_mode = stat.S_IMODE(public_key_path.stat().st_mode)
        assert private_mode == 0o600
        assert public_mode == 0o644

    assert "Public key fingerprint (SHA256):" in combined_output
    assert "BEGIN PRIVATE KEY" not in combined_output

    private_key = load_ed25519_private_key(private_key_path)
    public_key = load_ed25519_public_key(public_key_path)
    payload = b"feature40-keygen-payload"
    signature = sign_payload(private_key, payload)

    assert verify_signature(public_key, payload, signature) is True
    assert verify_signature(public_key, b"tampered", signature) is False


def test_init_language_python(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT_PATH),
            "init",
            "feature46-language-python",
            "--language",
            "python",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"init failed: {result.stdout}\n{result.stderr}"
    agent_dir = tmp_path / "feature46-language-python"
    assert (agent_dir / "run.py").exists()
    manifest_text = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "language: python" in manifest_text


def test_init_incompatible_framework_language(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT_PATH),
            "init",
            "feature46-language-invalid",
            "--framework",
            "openclaw",
            "--language",
            "python",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    combined = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Incompatible --framework/--language combination" in combined


def test_import_github_url(monkeypatch, tmp_path):
    from kinnoo import import_command
    from kinnoo.cli import main

    source_repo = tmp_path / "source-repo"
    source_repo.mkdir()
    (source_repo / "run.py").write_text("print('hello')\n", encoding="utf-8")

    def _fake_clone(_url: str, destination: Path) -> tuple[bool, str]:
        shutil.copytree(source_repo, destination)
        return True, ""

    monkeypatch.setattr(import_command, "clone_github_repo", _fake_clone)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "y")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kinnoo",
            "import",
            "https://github.com/acme/feature46-agent",
            str(tmp_path / "downloaded-agent"),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    assert (tmp_path / "downloaded-agent" / "kinnoo.yaml").exists()


def test_import_url_collision_error(monkeypatch, tmp_path):
    from kinnoo.cli import main

    existing_target = tmp_path / "existing-import-target"
    existing_target.mkdir()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kinnoo",
            "import",
            "https://github.com/acme/feature46-agent",
            str(existing_target),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_import_url_download_failure(monkeypatch, tmp_path):
    from kinnoo import import_command
    from kinnoo.cli import main

    def _fake_clone(_url: str, _destination: Path) -> tuple[bool, str]:
        return False, "repository URL not found or not accessible"

    monkeypatch.setattr(import_command, "clone_github_repo", _fake_clone)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "kinnoo",
            "import",
            "https://github.com/acme/missing-agent",
            str(tmp_path / "missing-agent"),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_check_command_local_pass(tmp_path):
    agent_dir = tmp_path / "feature46-check-pass"
    agent_dir.mkdir()
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature46-check-pass
version: 0.1.0
entrypoint: run.py
runtime:
  language: python
  version: \">=3.10\"
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""",
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "check", str(agent_dir)],
        capture_output=True,
        text=True,
    )

    combined = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined
    assert "Check result: PASS" in combined
    assert "import compatibility" in combined
    assert "inspect" in combined
    assert "preflight" in combined


def test_check_command_intelligent_failure(tmp_path):
    broken_agent_dir = tmp_path / "feature46-check-fail"
    broken_agent_dir.mkdir()
    (broken_agent_dir / "kinnoo.yaml").write_text(
        """
name: feature46-check-fail
version: 0.1.0
entrypoint: missing.py
runtime:
  language: python
  version: \">=3.10\"
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""",
        encoding="utf-8",
    )
    (broken_agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "check", str(broken_agent_dir)],
        capture_output=True,
        text=True,
    )

    combined = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "Check result: FAIL" in combined
    assert "Guidance" in combined


def test_colored_output_tty(tmp_path):
    agent_dir = tmp_path / "feature46-color-pass"
    agent_dir.mkdir()
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature46-color-pass
version: 0.1.0
entrypoint: run.py
runtime:
  language: python
  version: \">=3.10\"
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""",
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    env = dict(os.environ)
    env["KINNOO_FORCE_COLOR"] = "1"

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(agent_dir), "--preflight"],
        capture_output=True,
        text=True,
        env=env,
    )

    combined = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined
    assert "\u001b[" in combined
    assert "Preflight result: PASS" in combined


def test_no_color_env_respected(tmp_path):
    agent_dir = tmp_path / "feature46-no-color"
    agent_dir.mkdir()
    (agent_dir / "kinnoo.yaml").write_text(
        """
name: feature46-no-color
version: 0.1.0
entrypoint: run.py
runtime:
  language: python
  version: \">=3.10\"
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""",
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    env = dict(os.environ)
    env["KINNOO_FORCE_COLOR"] = "1"
    env["NO_COLOR"] = "1"

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "run", str(agent_dir), "--preflight"],
        capture_output=True,
        text=True,
        env=env,
    )

    combined = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined
    assert "\u001b[" not in combined


@pytest.mark.integration
def test_e2e_python_oneshot(tmp_path):
    """Feature47 test400: import/pack/install/run succeeds for a one-shot Python agent."""
    source_agent_dir = tmp_path / "feature47-e2e-python-agent"
    source_agent_dir.mkdir(parents=True, exist_ok=True)
    (source_agent_dir / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(f'e2e-python:{sys.argv[1]}')\n",
        encoding="utf-8",
    )
    (source_agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    env = dict(os.environ)
    env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")

    import_result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT_PATH), "import", str(source_agent_dir), "--force"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert import_result.returncode == 0, (
        f"kinnoo import failed: {import_result.stdout}\n{import_result.stderr}"
    )

    pack_result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT_PATH), "pack", str(source_agent_dir)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert pack_result.returncode == 0, (
        f"kinnoo pack failed: {pack_result.stdout}\n{pack_result.stderr}"
    )

    archive_path = tmp_path / "archive-root" / "feature47-e2e-python-agent" / "1.0.0" / "feature47-e2e-python-agent.kno"
    assert archive_path.exists(), f"Expected archive not found: {archive_path}"

    install_result = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT_PATH),
            "install",
            str(archive_path),
            "--yes",
            "--allow-unverified-publisher",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert install_result.returncode == 0, (
        f"kinnoo install failed: {install_result.stdout}\n{install_result.stderr}"
    )

    installed_agent_dir = tmp_path / "feature47-e2e-python-agent"
    assert installed_agent_dir.exists(), f"Installed agent dir not found: {installed_agent_dir}"

    run_result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT_PATH), "run", str(installed_agent_dir), "hello-e2e"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert run_result.returncode == 0, f"kinnoo run failed: {run_result.stdout}\n{run_result.stderr}"
    assert "e2e-python:hello-e2e" in run_result.stdout


@pytest.mark.integration
def test_e2e_mcp_server(tmp_path):
    """Feature47 test401: import/pack/install/run succeeds for an MCP-server runtime agent."""
    source_agent_dir = tmp_path / "feature47-e2e-mcp-server"
    source_agent_dir.mkdir(parents=True, exist_ok=True)
    (source_agent_dir / "run.py").write_text(
        "import time\n"
        "if __name__ == '__main__':\n"
        "    print('mcp-server-started', flush=True)\n"
        "    time.sleep(0.2)\n"
        "    print('mcp-server-ready', flush=True)\n",
        encoding="utf-8",
    )
    (source_agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    env = dict(os.environ)
    env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")

    import_result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT_PATH), "import", str(source_agent_dir), "--force"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert import_result.returncode == 0, (
        f"kinnoo import failed: {import_result.stdout}\n{import_result.stderr}"
    )

    manifest_path = source_agent_dir / "kinnoo.yaml"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_text = manifest_text.replace("type: one-shot", "type: mcp-server", 1)
    manifest_path.write_text(manifest_text, encoding="utf-8")

    pack_result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT_PATH), "pack", str(source_agent_dir)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert pack_result.returncode == 0, (
        f"kinnoo pack failed: {pack_result.stdout}\n{pack_result.stderr}"
    )

    archive_path = tmp_path / "archive-root" / "feature47-e2e-mcp-server" / "1.0.0" / "feature47-e2e-mcp-server.kno"
    assert archive_path.exists(), f"Expected archive not found: {archive_path}"

    install_result = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT_PATH),
            "install",
            str(archive_path),
            "--yes",
            "--allow-unverified-publisher",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert install_result.returncode == 0, (
        f"kinnoo install failed: {install_result.stdout}\n{install_result.stderr}"
    )

    installed_agent_dir = tmp_path / "feature47-e2e-mcp-server"
    assert installed_agent_dir.exists(), f"Installed agent dir not found: {installed_agent_dir}"

    run_result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT_PATH), "run", str(installed_agent_dir), "ping"],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert run_result.returncode == 0, f"kinnoo run failed: {run_result.stdout}\n{run_result.stderr}"
    combined = f"{run_result.stdout}\n{run_result.stderr}"
    assert "mcp-server-started" in combined


@pytest.mark.integration
def test_streamlit_import_daemon(tmp_path):
    """Feature47 test404: streamlit import emits daemon runtime with streamlit run command."""
    agent_dir = tmp_path / "streamlit-import-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "app.py").write_text(
        "import streamlit as st\n"
        "st.title('Demo')\n"
        "st.chat_input('Ask something')\n",
        encoding="utf-8",
    )

    import_result = subprocess.run(
        [sys.executable, str(CLI_SCRIPT_PATH), "import", str(agent_dir), "--force"],
        capture_output=True,
        text=True,
    )
    assert import_result.returncode == 0, (
        f"kinnoo import failed: {import_result.stdout}\n{import_result.stderr}"
    )

    manifest_text = (agent_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "type: daemon" in manifest_text
    assert "run_command: streamlit run" in manifest_text


def test_streamlit_run_command(tmp_path, monkeypatch):
    """Feature47 test405: run uses runtime.run_command override for Streamlit daemon agents."""
    from kinnoo import run_command

    agent_dir = tmp_path / "streamlit-run-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "app.py").write_text("print('streamlit app')\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "name: streamlit-run-agent\n"
        "version: 0.1.0\n"
        "entrypoint: app.py\n"
        "runtime:\n"
        "  language: python\n"
        "  version: \">=3.10\"\n"
        "  type: daemon\n"
        "  run_command: streamlit run app.py\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "  required: false\n"
        "outputs:\n"
        "  type: text\n",
        encoding="utf-8",
    )

    captured_args: list[list[str]] = []

    class _FakeProcess:
        def __init__(self) -> None:
            self.pid = 43210

    def _fake_popen(args, **kwargs):
        captured_args.append(list(args))
        return _FakeProcess()

    monkeypatch.setattr(run_command.subprocess, "Popen", _fake_popen)

    exit_code = run_command.run_agent(str(agent_dir), None)

    assert exit_code == 0
    assert captured_args, "Expected daemon launcher to invoke subprocess.Popen"
    assert captured_args[0][:3] == ["streamlit", "run", "app.py"]


def _create_feature66_openclaw_agent_dir(tmp_path, agent_name: str = "feature66-openclaw-agent"):
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "index.js").write_text("console.log('openclaw skill run')\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        "name: feature66-openclaw-agent\n"
        "version: 1.0.0\n"
        "type: openclaw-skill\n"
        "framework: openclaw\n"
        "entrypoint: index.js\n"
        "runtime:\n"
        "  language: nodejs\n"
        "  version: \">=20\"\n"
        "  type: daemon\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
        "provenance:\n"
        "  source_registry: clawhub\n"
        "  source_slug: feature66/sample\n"
        "  source_version: 1.0.0\n",
        encoding="utf-8",
    )
    return agent_dir


def _create_feature81_openclaw_agent_dir(tmp_path, agent_name: str = "feature81-openclaw-agent"):
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "index.js").write_text("console.log('openclaw feature81 run')\n", encoding="utf-8")
    (agent_dir / "kinnoo.yaml").write_text(
        f"name: {agent_name}\n"
        "version: 1.0.0\n"
        "type: openclaw-skill\n"
        "framework: openclaw\n"
        "entrypoint: index.js\n"
        "runtime:\n"
        "  language: nodejs\n"
        "  version: \">=20\"\n"
        "  type: daemon\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n",
        encoding="utf-8",
    )
    return agent_dir


def _make_feature81_fake_openclaw_cli(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    openclaw_script = bin_dir / "openclaw"
    openclaw_script.write_text(
        "#!/bin/sh\n"
        "if [ -n \"$KINNOO_TEST_OPENCLAW_RUN_LOG\" ]; then\n"
        "  printf '%s\\n' \"$*\" >> \"$KINNOO_TEST_OPENCLAW_RUN_LOG\"\n"
        "fi\n"
        "if [ \"$KINNOO_TEST_OPENCLAW_FAIL_RUN\" = \"1\" ]; then\n"
        "  echo simulated openclaw runtime failure >&2\n"
        "  exit 9\n"
        "fi\n"
        "if [ \"$1\" = \"agent\" ]; then\n"
        "  echo delegated-agent-ok\n"
        "  exit 0\n"
        "fi\n"
        "echo unsupported openclaw invocation >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    openclaw_script.chmod(0o755)


def test_feature81_run_mapping_thinking_and_exit_propagation(tmp_path):
    agent_dir = _create_feature81_openclaw_agent_dir(tmp_path)
    fake_bin = tmp_path / "feature81-openclaw-bin"
    _make_feature81_fake_openclaw_cli(fake_bin)
    invocation_log = tmp_path / "feature81-openclaw-run.log"

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    env["KINNOO_TEST_OPENCLAW_RUN_LOG"] = str(invocation_log)

    success_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello-openclaw",
            "--thinking",
            "high",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    success_output = f"{success_result.stdout}\n{success_result.stderr}"
    assert success_result.returncode == 0, success_output
    assert "delegated invocation" in success_output

    logged_invocations = invocation_log.read_text(encoding="utf-8")
    assert "agent --agent feature81-openclaw-agent --message hello-openclaw --thinking high" in logged_invocations

    failing_env = dict(env)
    failing_env["KINNOO_TEST_OPENCLAW_FAIL_RUN"] = "1"
    failing_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello-openclaw",
        ],
        capture_output=True,
        text=True,
        env=failing_env,
    )
    failing_output = f"{failing_result.stdout}\n{failing_result.stderr}"
    assert failing_result.returncode == 9
    assert "openclaw_agent_runtime_nonzero_exit" in failing_output


def _make_feature66_fake_openclaw_cli(bin_dir: Path, *, version: str = "0.3.0") -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    openclaw_script = bin_dir / "openclaw"
    openclaw_script.write_text(
        "#!/bin/sh\n"
        "if [ -n \"$KINNOO_TEST_OPENCLAW_RUN_LOG\" ]; then\n"
        "  printf '%s\\n' \"$*\" >> \"$KINNOO_TEST_OPENCLAW_RUN_LOG\"\n"
        "fi\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        f"  echo v{version}\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$KINNOO_TEST_OPENCLAW_FAIL_RUN\" = \"1\" ]; then\n"
        "  echo simulated adapter backend failure >&2\n"
        "  exit 7\n"
        "fi\n"
        "if [ \"$1\" = \"skills\" ] && [ \"$2\" = \"run\" ] && [ \"$3\" = \".\" ]; then\n"
        "  echo adapter-native-ok\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"run\" ] && [ \"$2\" = \".\" ]; then\n"
        "  echo adapter-legacy-ok\n"
        "  exit 0\n"
        "fi\n"
        "echo unsupported openclaw adapter invocation >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    openclaw_script.chmod(0o755)


def test_feature66_run_adapter_backend_selection_and_gate(tmp_path):
    agent_dir = _create_feature66_openclaw_agent_dir(tmp_path)

    gate_disabled = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello",
        ],
        capture_output=True,
        text=True,
    )
    gate_disabled_output = f"{gate_disabled.stdout}\n{gate_disabled.stderr}"
    assert gate_disabled.returncode != 0
    assert "experimental and disabled by default" in gate_disabled_output
    assert "--experimental-openclaw-adapter" in gate_disabled_output

    fake_bin = tmp_path / "feature66-openclaw-bin"
    _make_feature66_fake_openclaw_cli(fake_bin, version="0.3.0")
    invocation_log = tmp_path / "feature66-openclaw-run.log"

    enabled_env = dict(os.environ)
    enabled_env["PATH"] = f"{fake_bin}{os.pathsep}{enabled_env.get('PATH', '')}"
    enabled_env["KINNOO_TEST_OPENCLAW_RUN_LOG"] = str(invocation_log)

    gate_enabled = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello",
            "--experimental-openclaw-adapter",
        ],
        capture_output=True,
        text=True,
        env=enabled_env,
    )
    gate_enabled_output = f"{gate_enabled.stdout}\n{gate_enabled.stderr}"
    assert gate_enabled.returncode == 0, gate_enabled_output
    assert "openclaw_adapter_backend_native_skills_run" in gate_enabled_output
    assert "backend=native-skills-run" in gate_enabled_output
    assert "command=openclaw skills run . hello" in gate_enabled_output

    invocations = invocation_log.read_text(encoding="utf-8").splitlines()
    assert "--version" in invocations
    assert "skills run . hello" in invocations


def test_feature66_run_adapter_diagnostics_and_failures(tmp_path):
    agent_dir = _create_feature66_openclaw_agent_dir(tmp_path)

    # Missing backend case.
    missing_backend = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello",
            "--experimental-openclaw-adapter",
        ],
        capture_output=True,
        text=True,
    )
    missing_backend_output = f"{missing_backend.stdout}\n{missing_backend.stderr}"
    assert missing_backend.returncode != 0
    assert "category=openclaw_adapter_cli_missing" in missing_backend_output

    # Unsupported version case.
    unsupported_bin = tmp_path / "feature66-openclaw-unsupported-bin"
    _make_feature66_fake_openclaw_cli(unsupported_bin, version="0.1.0")
    unsupported_env = dict(os.environ)
    unsupported_env["PATH"] = f"{unsupported_bin}{os.pathsep}{unsupported_env.get('PATH', '')}"

    unsupported_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello",
            "--experimental-openclaw-adapter",
        ],
        capture_output=True,
        text=True,
        env=unsupported_env,
    )
    unsupported_output = f"{unsupported_result.stdout}\n{unsupported_result.stderr}"
    assert unsupported_result.returncode != 0
    assert "openclaw_adapter_version_unsupported" in unsupported_output
    assert "requires >= 0.2.0" in unsupported_output

    # Runtime non-zero delegated backend case.
    failing_bin = tmp_path / "feature66-openclaw-failing-bin"
    _make_feature66_fake_openclaw_cli(failing_bin, version="0.3.0")
    failing_env = dict(os.environ)
    failing_env["PATH"] = f"{failing_bin}{os.pathsep}{failing_env.get('PATH', '')}"
    failing_env["KINNOO_TEST_OPENCLAW_FAIL_RUN"] = "1"

    failing_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello",
            "--experimental-openclaw-adapter",
        ],
        capture_output=True,
        text=True,
        env=failing_env,
    )
    failing_output = f"{failing_result.stdout}\n{failing_result.stderr}"
    assert failing_result.returncode == 7
    assert "category=openclaw_adapter_runtime_nonzero_exit" in failing_output
    assert "simulated adapter backend failure" in failing_output

    # New test for feature73
def test_feature73_diff_manifest_and_files(tmp_path):
    archive_a = tmp_path / "feature73-a.kno"
    archive_b = tmp_path / "feature73-b.kno"

    manifest_a = (
        "name: feature73-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  language: python\n"
        "  version: \">=3.10\"\n"
        "  type: one-shot\n"
        "dependencies:\n"
        "  - requests\n"
        "env_vars:\n"
        "  - API_KEY\n"
        "permissions:\n"
        "  network: false\n"
        "  shell: false\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )

    manifest_b = (
        "name: feature73-agent\n"
        "version: 1.1.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  language: python\n"
        "  version: \">=3.10\"\n"
        "  type: one-shot\n"
        "dependencies:\n"
        "  - requests\n"
        "  - httpx\n"
        "env_vars:\n"
        "  - API_KEY\n"
        "  - DEBUG\n"
        "permissions:\n"
        "  network: true\n"
        "  shell: false\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )

    with zipfile.ZipFile(archive_a, "w") as zip_a:
        zip_a.writestr("kinnoo.yaml", manifest_a)
        zip_a.writestr("run.py", "print('v1')\n")
        zip_a.writestr("keep.txt", "same\n")
        zip_a.writestr("removed.txt", "remove-me\n")

    with zipfile.ZipFile(archive_b, "w") as zip_b:
        zip_b.writestr("kinnoo.yaml", manifest_b)
        zip_b.writestr("run.py", "print('v2')\n")
        zip_b.writestr("keep.txt", "same\n")
        zip_b.writestr("added.txt", "add-me\n")

    result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "diff",
            str(archive_a),
            str(archive_b),
        ],
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 2, output
    assert "Manifest changes:" in output
    assert "dependencies: added=['httpx'] removed=[]" in output
    assert "env_vars: added=['DEBUG'] removed=[]" in output
    assert "permissions: from={\"network\": false, \"shell\": false}" in output
    assert "File changes:" in output
    assert "- added: added.txt" in output
    assert "- removed: removed.txt" in output
    assert "- modified: kinnoo.yaml, run.py" in output


def test_feature73_diff_json_and_exit_codes(tmp_path):
    identical_a = tmp_path / "feature73-identical-a.kno"
    identical_b = tmp_path / "feature73-identical-b.kno"
    different_b = tmp_path / "feature73-different-b.kno"

    identical_manifest = (
        "name: feature73-json-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  language: python\n"
        "  version: \">=3.10\"\n"
        "  type: one-shot\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )

    different_manifest = (
        "name: feature73-json-agent\n"
        "version: 1.1.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  language: python\n"
        "  version: \">=3.10\"\n"
        "  type: one-shot\n"
        "dependencies:\n"
        "  - requests\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )

    with zipfile.ZipFile(identical_a, "w") as archive:
        archive.writestr("kinnoo.yaml", identical_manifest)
        archive.writestr("run.py", "print('same')\n")

    with zipfile.ZipFile(identical_b, "w") as archive:
        archive.writestr("kinnoo.yaml", identical_manifest)
        archive.writestr("run.py", "print('same')\n")

    with zipfile.ZipFile(different_b, "w") as archive:
        archive.writestr("kinnoo.yaml", different_manifest)
        archive.writestr("run.py", "print('different')\n")

    identical_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "diff",
            str(identical_a),
            str(identical_b),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert identical_result.returncode == 0, identical_result.stderr
    identical_payload = json.loads(identical_result.stdout)
    assert identical_payload["schema_version"] == "1.0"
    assert identical_payload["changes_detected"] is False
    assert identical_payload["manifest_changes"] == []
    assert identical_payload["file_changes"] == {
        "added": [],
        "removed": [],
        "modified": [],
    }

    different_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "diff",
            str(identical_a),
            str(different_b),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert different_result.returncode == 2, different_result.stderr
    different_payload = json.loads(different_result.stdout)
    assert different_payload["schema_version"] == "1.0"
    assert different_payload["changes_detected"] is True
    assert isinstance(different_payload["manifest_changes"], list)
    assert isinstance(different_payload["file_changes"], dict)

    missing_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "diff",
            str(identical_a),
            str(tmp_path / "missing.kno"),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert missing_result.returncode == 1
    assert "does not exist or is not a file" in missing_result.stderr
