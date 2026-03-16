import subprocess
import sys
from pathlib import Path
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


CLI_PATH = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"


def _create_agent_fixture(agent_dir: Path, *, with_manifest: bool = True) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)

    if with_manifest:
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: preflight-agent",
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

    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text(
        "from pathlib import Path\n"
        "Path('entrypoint-executed.flag').write_text('executed', encoding='utf-8')\n"
        "print('entrypoint-ran')\n",
        encoding="utf-8",
    )


def test_preflight_runs_checks_without_entrypoint_execution(tmp_path: Path) -> None:
    passing_agent = tmp_path / "preflight-pass-agent"
    _create_agent_fixture(passing_agent, with_manifest=True)

    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(passing_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "Preflight checklist:" in pass_output
    assert "[PASS] entrypoint execution path skipped in preflight mode" in pass_output
    assert "Preflight result: PASS" in pass_output
    assert not (tmp_path / "entrypoint-executed.flag").exists()

    failing_agent = tmp_path / "preflight-fail-agent"
    _create_agent_fixture(failing_agent, with_manifest=False)

    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(failing_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "Preflight checklist:" in fail_output
    assert "[FAIL] manifest exists" in fail_output
    assert "Preflight result: FAIL" in fail_output
    assert not (tmp_path / "entrypoint-executed.flag").exists()


def test_preflight_runtime_version_check(tmp_path: Path) -> None:
    runtime_pass_agent = tmp_path / "runtime-pass-agent"
    _create_agent_fixture(runtime_pass_agent, with_manifest=True)
    (runtime_pass_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: runtime-pass-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
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

    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(runtime_pass_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "[PASS] runtime version check passed" in pass_output
    assert "satisfies runtime.version '>=3.0'" in pass_output

    runtime_fail_agent = tmp_path / "runtime-fail-agent"
    _create_agent_fixture(runtime_fail_agent, with_manifest=True)
    (runtime_fail_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: runtime-fail-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=99.0\"",
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

    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(runtime_fail_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "[FAIL] runtime version check failed" in fail_output
    assert "does not satisfy runtime.version '>=99.0'" in fail_output
    assert "Action: use a Python interpreter that satisfies runtime.version in kinnoo.yaml" in fail_output


def test_preflight_env_vars_resolution_and_secret_safety(tmp_path: Path) -> None:
    env_pass_agent = tmp_path / "env-pass-agent"
    _create_agent_fixture(env_pass_agent, with_manifest=True)
    (env_pass_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: env-pass-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
                "  type: one-shot",
                "dependencies: []",
                "env_vars:",
                "  - API_TOKEN",
                "  - DB_KEY",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (env_pass_agent / ".env").write_text("DB_KEY=dotenv-secret-db-value\n", encoding="utf-8")

    env = {
        **os.environ,
        "API_TOKEN": "env-secret-api-token-value",
    }
    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(env_pass_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "[PASS] env vars check passed" in pass_output
    assert "resolved env vars [API_TOKEN, DB_KEY]" in pass_output
    assert "env-secret-api-token-value" not in pass_output
    assert "dotenv-secret-db-value" not in pass_output

    env_fail_agent = tmp_path / "env-fail-agent"
    _create_agent_fixture(env_fail_agent, with_manifest=True)
    (env_fail_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: env-fail-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
                "  type: one-shot",
                "dependencies: []",
                "env_vars:",
                "  - MISSING_TOKEN",
                "inputs:",
                "  type: text",
                "outputs:",
                "  type: text",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    fail_env = dict(os.environ)
    fail_env.pop("MISSING_TOKEN", None)
    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(env_fail_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=fail_env,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "[FAIL] env vars check failed" in fail_output
    assert "unresolved env vars [MISSING_TOKEN]" in fail_output
    assert "Action: set missing env vars in your shell environment or agent-local .env file" in fail_output


def test_preflight_entrypoint_and_dependency_checks(tmp_path: Path) -> None:
    missing_entrypoint_agent = tmp_path / "missing-entrypoint-agent"
    _create_agent_fixture(missing_entrypoint_agent, with_manifest=True)
    (missing_entrypoint_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: missing-entrypoint-agent",
                "version: 1.0.0",
                "entrypoint: does-not-exist.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
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

    missing_entrypoint_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(missing_entrypoint_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    missing_entrypoint_output = f"{missing_entrypoint_result.stdout}\n{missing_entrypoint_result.stderr}"

    assert missing_entrypoint_result.returncode != 0
    assert "[FAIL] entrypoint check failed" in missing_entrypoint_output
    assert "does-not-exist.py" in missing_entrypoint_output
    assert "Action: ensure manifest entrypoint exists and is readable" in missing_entrypoint_output

    dependency_fail_agent = tmp_path / "dependency-fail-agent"
    _create_agent_fixture(dependency_fail_agent, with_manifest=True)
    (dependency_fail_agent / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: dependency-fail-agent",
                "version: 1.0.0",
                "entrypoint: run.py",
                "runtime:",
                "  language: python",
                "  version: \">=3.0\"",
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
    (dependency_fail_agent / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    dependency_fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(dependency_fail_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    dependency_fail_output = f"{dependency_fail_result.stdout}\n{dependency_fail_result.stderr}"

    assert dependency_fail_result.returncode != 0
    assert "[FAIL] dependency readiness check failed" in dependency_fail_output
    assert "virtual environment not found" in dependency_fail_output
    assert "Action: create agent .venv and install requirements" in dependency_fail_output


def test_preflight_checklist_and_ready_summary(tmp_path: Path) -> None:
    pass_agent = tmp_path / "ready-pass-agent"
    _create_agent_fixture(pass_agent, with_manifest=True)

    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(pass_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "[PASS] runtime version check" in pass_output
    assert "[PASS] env vars check" in pass_output
    assert "[PASS] entrypoint check" in pass_output
    assert "[PASS] dependency readiness check" in pass_output
    assert "Ready to run" in pass_output
    assert "Not ready to run" not in pass_output

    fail_agent = tmp_path / "ready-fail-agent"
    _create_agent_fixture(fail_agent, with_manifest=True)
    (fail_agent / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(fail_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "[PASS] runtime version check" in fail_output
    assert "[PASS] env vars check" in fail_output
    assert "[PASS] entrypoint check" in fail_output
    assert "[FAIL] dependency readiness check" in fail_output
    assert "Not ready to run" in fail_output
    assert "Remediation summary:" in fail_output
    assert "- dependencies: create .venv and install requirements" in fail_output
    assert "Ready to run" not in fail_output


def test_feature25_preflight_includes_service_health_results(tmp_path: Path) -> None:
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

    agent_dir = tmp_path / "feature25-preflight-agent"
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text(
        "from pathlib import Path\n"
        "Path('feature25-entrypoint.flag').write_text('ran', encoding='utf-8')\n"
        "print('feature25-entrypoint-ran')\n",
        encoding="utf-8",
    )
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature25-preflight-agent",
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
                "      process_name: feature25-missing-process",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        result = subprocess.run(
            [sys.executable, str(CLI_PATH), "run", str(agent_dir), "--preflight"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode != 0
        assert "Service health checks:" in output
        assert "[PASS] service 'local-api'" in output
        assert "[PASS] service 'local-db'" in output
        assert "[FAIL] service 'local-redis'" in output
        assert "(type: local-process, method: process)" in output
        assert "Guidance:" in output
        assert "Preflight result: FAIL" in output
        assert not (tmp_path / "feature25-entrypoint.flag").exists()
    finally:
        stop_accept.set()
        tcp_socket.close()
        http_server.shutdown()
        http_server.server_close()
