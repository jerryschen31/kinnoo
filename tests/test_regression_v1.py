import os
import subprocess
import sys
import tempfile
import json
from pathlib import Path


# [agent] Run this regression gate before opening/merging PRs that change CLI behavior,
# command modules, packaging/install flows, or shared test utilities; it verifies V1
# baseline modules still pass together after refactors.
def test_v1_suite_passes_after_feature7():
    modules = [
        "tests/test_validator.py",
        "tests/test_init.py",
        "tests/test_cli.py",
        "tests/test_pack.py",
        "tests/test_install.py",
        "tests/test_cli_install.py",
    ]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *modules],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "V1 regression suite failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature20_does_not_regress_v2_behavior():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_cli.py",
        "-k",
        "run",
        "tests/test_install.py",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature20 regression gate failed for V2 run/install behavior.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature21_framework_templates_do_not_regress_existing_frameworks():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_init.py::test_framework_templates_generate_correct_files",
        "tests/test_init.py::test_framework_valid",
        "tests/test_init.py::test_framework_manifests_pass_validation",
        "tests/test_init.py::test_feature21_regression_existing_frameworks_unchanged",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature21 regression gate failed for existing framework templates.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature22_no_assets_regression_unchanged():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_pack.py::test_pack_creates_correct_archive_structure",
        "tests/test_cli_install_extract.py::test_install_extracts_archive",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature22 no-assets regression gate failed for pack/install behavior.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature23_no_regression_for_one_shot_runtime():
    """Regression gate: ensure one-shot execution semantics remain unchanged."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_cli.py::test_run_entrypoint_with_input",
        "tests/test_cli.py::test_run_streams_stdout_stderr",
        "tests/test_cli.py::test_run_exit_code",
        "tests/test_cli.py::test_run_single_input_backward_compatible",
        "tests/test_trust_baseline.py::test_run_trace_log_safe_fields",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature23 regression gate failed for one-shot runtime behavior.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature24_ac_coverage_and_no_services_regression_gate():
    """Regression gate for feature24 AC coverage and no-services compatibility."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_validator.py::test_feature24_services_optional_list_is_accepted",
        "tests/test_validator.py::test_feature24_service_required_fields_and_type_validation",
        "tests/test_validator.py::test_feature24_health_check_method_specific_validation",
        "tests/test_validator.py::test_feature24_no_services_regression_unchanged",
        "tests/test_validator.py::test_feature24_duplicate_service_names_rejected",
        "tests/test_cli_inspect.py::test_feature24_inspect_displays_services",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature24 regression gate failed for AC coverage and no-services compatibility.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature25_no_services_regression_unchanged():
    """Regression test: agents without services remain behaviorally unchanged."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        agent_dir = temp_path / "feature25-no-services-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)

        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "README.md").write_text("feature25 no-services fixture", encoding="utf-8")
        (agent_dir / "tools").mkdir()
        (agent_dir / "prompts").mkdir()
        (agent_dir / "run.py").write_text(
            "import sys\n"
            "print(f\"no-services-entrypoint:{sys.argv[1] if len(sys.argv) > 1 else ''}\")\n",
            encoding="utf-8",
        )
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: feature25-no-services-agent",
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
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, str(cli_path), "run", str(agent_dir), "hello"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, output
        assert "no-services-entrypoint:hello" in output
        assert "Service health checks:" not in output


def test_feature25_ac_coverage_and_no_services_regression_gate():
    """Regression gate for feature25 AC coverage and no-services compatibility."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_health_check.py::test_feature25_http_health_check_2xx_and_timeout",
        "tests/test_health_check.py::test_feature25_tcp_health_check_localhost_and_timeout",
        "tests/test_health_check.py::test_feature25_process_health_check",
        "tests/test_cli.py::test_feature25_run_checks_all_declared_services_before_entrypoint",
        "tests/test_run_preflight.py::test_feature25_preflight_includes_service_health_results",
        "tests/test_cli.py::test_feature25_non_interactive_aborts_on_unhealthy_service",
        "tests/test_cli.py::test_feature25_interactive_prompt_allows_proceed_or_abort",
        "tests/test_regression_v1.py::test_feature25_no_services_regression_unchanged",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature25 regression gate failed for AC coverage and no-services compatibility.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature26_framework_template_regression_gate():
    """Regression gate: existing init frameworks remain stable after adding mcp-client."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_init.py::test_framework_templates_generate_correct_files",
        "tests/test_init.py::test_framework_valid",
        "tests/test_init.py::test_framework_manifests_pass_validation",
        "tests/test_init.py::test_feature21_regression_existing_frameworks_unchanged",
        "tests/test_init.py::test_feature26_mcp_client_template_generation",
        "tests/test_init.py::test_feature26_mcp_client_template_contract_and_validation",
        "tests/test_validator.py::test_feature26_permissions_schema_validation",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature26 regression gate failed for framework template stability and permissions validation.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature19_import_interrupt_and_runnability_regression_gate():
    """Regression gate for task167 interruption safety and in-place runnability."""
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_cli_import.py::test_feature19_interrupt_cleanup_and_exit_code",
        "tests/test_cli_import.py::test_feature19_imported_project_runs_in_place",
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Feature19 regression gate failed for interruption safety and runnability.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )


def test_feature31_python_runtime_regression_gate():
    """Regression gate: feature31 Node support must not alter Python run/pack/install behavior."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_root = temp_path / "archive-root"
        env = os.environ.copy()
        env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

        agent_dir = temp_path / "feature31-python-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: feature31-python-agent",
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
        (agent_dir / "run.py").write_text(
            "import sys\n"
            "print(f\"feature31-python-output:{sys.argv[1] if len(sys.argv) > 1 else ''}\")\n",
            encoding="utf-8",
        )
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

        pack_result = subprocess.run(
            [sys.executable, str(cli_path), "pack", str(agent_dir)],
            cwd=temp_path,
            capture_output=True,
            text=True,
            env=env,
        )
        assert pack_result.returncode == 0, (
            "Feature31 python regression gate failed during pack.\n"
            f"STDOUT:\n{pack_result.stdout}\n"
            f"STDERR:\n{pack_result.stderr}"
        )

        archive_path = archive_root / "feature31-python-agent" / "1.0.0" / "feature31-python-agent.kno"
        assert archive_path.exists(), "Expected packed archive for feature31 python regression gate"

        installed_dir = temp_path / "feature31-python-installed"
        install_result = subprocess.run(
            [sys.executable, str(cli_path), "install", str(archive_path), str(installed_dir), "--yes"],
            cwd=temp_path,
            capture_output=True,
            text=True,
            env=env,
        )
        assert install_result.returncode == 0, (
            "Feature31 python regression gate failed during install.\n"
            f"STDOUT:\n{install_result.stdout}\n"
            f"STDERR:\n{install_result.stderr}"
        )

        run_result = subprocess.run(
            [sys.executable, str(cli_path), "run", str(installed_dir), "hello-python"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            env=env,
        )
        output = f"{run_result.stdout}\n{run_result.stderr}"
        assert run_result.returncode == 0, output
        assert "feature31-python-output:hello-python" in output


def test_feature42_json_contract_guidance_and_text_regression_gate():
    """Regression gate for feature42 docs/help/inspect/preflight guidance and text-flow stability."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_path = repo_root / "src" / "kinnoo" / "cli.py"
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    docs_text = f"{schema_doc.read_text(encoding='utf-8')}\n{readme_doc.read_text(encoding='utf-8')}"
    assert "--json-input" in docs_text
    assert "--json-file" in docs_text
    assert "stdout must be valid JSON" in docs_text

    run_help_result = subprocess.run(
        [sys.executable, str(cli_path), "run", "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert run_help_result.returncode == 0, run_help_result.stderr
    assert "--json-input" in run_help_result.stdout
    assert "--json-file" in run_help_result.stdout

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        agent_dir = temp_path / "feature42-guidance-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "run.py").write_text("import json\nprint(json.dumps({'ok': True}))\n", encoding="utf-8")
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: feature42-guidance-agent",
                    "version: 1.0.0",
                    "entrypoint: run.py",
                    "runtime:",
                    "  language: python",
                    "  version: \">=3.10\"",
                    "  type: one-shot",
                    "dependencies: []",
                    "inputs:",
                    "  type: json",
                    "outputs:",
                    "  type: json",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        preflight_result = subprocess.run(
            [sys.executable, str(cli_path), "run", str(agent_dir), "--preflight"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        preflight_output = f"{preflight_result.stdout}\n{preflight_result.stderr}"
        assert preflight_result.returncode == 0, preflight_output
        assert "manifest I/O contract: inputs.type [json], outputs.type [json]" in preflight_output
        assert "--json-input or --json-file" in preflight_output
        assert "stdout must be valid JSON" in preflight_output

        inspect_result = subprocess.run(
            [sys.executable, str(cli_path), "inspect", str(agent_dir)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        inspect_output = f"{inspect_result.stdout}\n{inspect_result.stderr}"
        assert inspect_result.returncode == 0, inspect_output
        assert "- Input Types: json" in inspect_output
        assert "- Output Types: json" in inspect_output
        assert "- JSON Contract:" in inspect_output

    regression_command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_regression_v1.py::test_feature31_python_runtime_regression_gate",
        "tests/test_cli.py::test_feature31_run_nodejs_entrypoint_streams_and_propagates_exit",
        "tests/test_cli.py::test_run_single_input_backward_compatible",
        "tests/test_docs.py::test_feature42_docs_cover_json_contract_guidance",
    ]
    regression_result = subprocess.run(
        regression_command,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert regression_result.returncode == 0, (
        "Feature42 regression gate failed for guidance surfaces and text flow compatibility.\n"
        f"STDOUT:\n{regression_result.stdout}\n"
        f"STDERR:\n{regression_result.stderr}"
    )


def test_feature32_daemon_health_state_regression_gate(tmp_path, monkeypatch, capsys):
    """Regression gate: daemon lifecycle reports not-running/unhealthy/healthy with compatibility checks."""
    import kinnoo.run_command as run_command

    def _write_manifest(agent_dir: Path, runtime_type: str) -> None:
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    f"name: {agent_dir.name}",
                    "version: 1.0.0",
                    "entrypoint: run.py",
                    "runtime:",
                    "  language: python",
                    "  version: \">=3.10\"",
                    f"  type: {runtime_type}",
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
        (agent_dir / "run.py").write_text("print('ok')\n", encoding="utf-8")

    healthy_agent = tmp_path / "feature32-daemon-healthy"
    healthy_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(healthy_agent, "daemon")
    healthy_state = healthy_agent / ".kinnoo" / "daemon-state.json"
    healthy_state.parent.mkdir(parents=True, exist_ok=True)
    healthy_state.write_text(json.dumps({"pid": 55001}), encoding="utf-8")

    unhealthy_agent = tmp_path / "feature32-daemon-unhealthy"
    unhealthy_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(unhealthy_agent, "daemon")
    unhealthy_state = unhealthy_agent / ".kinnoo" / "daemon-state.json"
    unhealthy_state.parent.mkdir(parents=True, exist_ok=True)
    unhealthy_state.write_text(json.dumps({"pid": 55002}), encoding="utf-8")

    not_running_agent = tmp_path / "feature32-daemon-not-running"
    not_running_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(not_running_agent, "daemon")

    one_shot_agent = tmp_path / "feature32-one-shot-compat"
    one_shot_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(one_shot_agent, "one-shot")

    mcp_agent = tmp_path / "feature32-mcp-compat"
    mcp_agent.mkdir(parents=True, exist_ok=True)
    _write_manifest(mcp_agent, "mcp-server")

    def fake_run_service_checks(manifest: dict | None):
        if not isinstance(manifest, dict):
            return []
        agent_name = str(manifest.get("name", ""))
        if "unhealthy" in agent_name:
            return [
                run_command.HealthCheckResult(
                    service_name="backend",
                    service_type="http",
                    method="http",
                    healthy=False,
                    message="mock unhealthy service",
                    guidance="mock guidance",
                )
            ]
        return []

    def fake_pid_running(pid: int) -> bool:
        return pid in (55001, 55002)

    monkeypatch.setattr(run_command, "_run_service_checks", fake_run_service_checks)
    monkeypatch.setattr(run_command, "daemon_pid_is_running", fake_pid_running)

    healthy_code = run_command.run_preflight(str(healthy_agent))
    healthy_capture = capsys.readouterr()
    healthy_output = f"{healthy_capture.out}\n{healthy_capture.err}"
    assert healthy_code == 0, healthy_output
    assert "daemon lifecycle state [healthy]" in healthy_output

    unhealthy_code = run_command.run_preflight(str(unhealthy_agent))
    unhealthy_capture = capsys.readouterr()
    unhealthy_output = f"{unhealthy_capture.out}\n{unhealthy_capture.err}"
    assert unhealthy_code != 0, unhealthy_output
    assert "daemon lifecycle state [unhealthy]" in unhealthy_output
    assert "services[].health_check" in unhealthy_output or "service checks" in unhealthy_output

    not_running_code = run_command.run_preflight(str(not_running_agent))
    not_running_capture = capsys.readouterr()
    not_running_output = f"{not_running_capture.out}\n{not_running_capture.err}"
    assert not_running_code != 0, not_running_output
    assert "daemon lifecycle state [not-running]" in not_running_output
    assert "Start daemon" in not_running_output

    one_shot_code = run_command.run_preflight(str(one_shot_agent))
    one_shot_capture = capsys.readouterr()
    one_shot_output = f"{one_shot_capture.out}\n{one_shot_capture.err}"
    assert one_shot_code == 0, one_shot_output
    assert "daemon lifecycle state" not in one_shot_output

    mcp_code = run_command.run_preflight(str(mcp_agent))
    mcp_capture = capsys.readouterr()
    mcp_output = f"{mcp_capture.out}\n{mcp_capture.err}"
    assert mcp_code == 0, mcp_output
    assert "daemon lifecycle state" not in mcp_output

