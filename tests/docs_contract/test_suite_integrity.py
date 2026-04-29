import ast
import re
from pathlib import Path
from collections import Counter

import yaml


# [agent] Run this check whenever tests are added/renamed/refactored (especially in
# task41+ follow-ups) to prevent duplicate test function names that cause ambiguous
# collection and flaky suite behavior.
def _collect_test_function_definitions() -> list[tuple[str, str, int]]:
    test_defs: list[tuple[str, str, int]] = []
    for path in sorted(Path("tests").glob("test_*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_defs.append((node.name, str(path), node.lineno))
    return test_defs


def test_no_duplicate_test_functions():
    test_defs = _collect_test_function_definitions()

    name_counts = Counter(name for name, _, _ in test_defs)
    duplicate_names = {name for name, count in name_counts.items() if count > 1}

    detailed_duplicates = {
        name: [(path, lineno) for test_name, path, lineno in test_defs if test_name == name]
        for name in duplicate_names
    }

    assert not detailed_duplicates, f"Duplicate test function names found: {detailed_duplicates}"


def test_feature68_workflow_secret_env_guards() -> None:
    workflow_path = Path(".github/workflows/kinnoo-publish.yml")
    assert workflow_path.exists(), "Expected Feature68 reference workflow to exist"

    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow_data = yaml.safe_load(workflow_text)
    assert isinstance(workflow_data, dict)

    jobs = workflow_data.get("jobs")
    assert isinstance(jobs, dict)
    publish_job = jobs.get("publish")
    assert isinstance(publish_job, dict)

    env = publish_job.get("env")
    assert isinstance(env, dict)
    assert env.get("KINNOO_REGISTRY_URL") == "${{ secrets.KINNOO_REGISTRY_URL }}"
    assert env.get("KINNOO_REGISTRY_TOKEN") == "${{ secrets.KINNOO_REGISTRY_TOKEN }}"
    assert env.get("KINNOO_TENANT_SLUG") == "${{ secrets.KINNOO_TENANT_SLUG }}"

    assert "[[ -n \"${KINNOO_REGISTRY_URL}\" ]]" in workflow_text
    assert "[[ -n \"${KINNOO_REGISTRY_TOKEN}\" ]]" in workflow_text
    assert "[[ -n \"${KINNOO_TENANT_SLUG}\" ]]" in workflow_text
    assert "Missing secret: KINNOO_REGISTRY_URL" in workflow_text
    assert "Missing secret: KINNOO_REGISTRY_TOKEN" in workflow_text
    assert "Missing secret: KINNOO_TENANT_SLUG" in workflow_text
    assert "set -euo pipefail" in workflow_text


def test_feature116_cli_helpers_cover_all_active_commands() -> None:
    cli_path = Path("src/kinnoo/cli.py")
    helper_path = Path("tests/helpers.py")
    assert cli_path.exists(), "Expected CLI entrypoint file"
    assert helper_path.exists(), "Expected shared helper module"

    cli_text = cli_path.read_text(encoding="utf-8")
    helper_text = helper_path.read_text(encoding="utf-8")

    expected_commands = [
        "init",
        "run",
        "test",
        "install",
        "pack",
        "diff",
        "fetch",
        "uninstall",
        "keygen",
        "inspect",
        "publish",
        "list",
        "search",
        "login",
        "logout",
        "import",
        "check",
    ]

    for command in expected_commands:
        parser_pattern = rf"add_parser\(\s*['\"]{re.escape(command)}['\"]"
        assert re.search(parser_pattern, cli_text), f"CLI parser for {command} missing"
        assert f'"{command}"' in helper_text, f"helpers missing command entry for {command}"
        assert f"def run_{command.replace('-', '_')}(" in helper_text, (
            f"helpers missing run helper for {command}"
        )


def test_feature116_marker_docs_and_test_agent_contracts_present() -> None:
    pyproject_path = Path("pyproject.toml")
    readme_path = Path("tests/README.md")
    test_agent_path = Path(".github/test.agent.md")

    assert pyproject_path.exists(), "Expected pyproject marker config"
    assert readme_path.exists(), "Expected tests marker guide"
    assert test_agent_path.exists(), "Expected dedicated test agent guidance"

    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")
    agent_text = test_agent_path.read_text(encoding="utf-8")

    for marker in [
        "regression_unit",
        "regression_integration",
        "regression_smoke",
        "schema_contract",
        "schema_unit",
        "integration",
        "client_cli",
        "client_cli_registry",
        "e2e",
        "registry_remote",
        "security_checks",
    ]:
        assert marker in pyproject_text, f"Missing marker in pyproject: {marker}"
        assert marker in readme_text, f"Missing marker in tests README: {marker}"

    assert "Deprecation-on-Removal Workflow" in agent_text
    assert "validate_manifest_data(data)" in agent_text
