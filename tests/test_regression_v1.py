import subprocess
import sys
import tempfile
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
