import ast
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
