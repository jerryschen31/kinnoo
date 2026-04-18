import ast
from pathlib import Path
from collections import Counter


# [agent] Run this check whenever tests are added/renamed/refactored (especially in
# task41+ follow-ups) to prevent duplicate test function names that cause ambiguous
# collection and flaky suite behavior.
def _collect_test_function_definitions() -> list[tuple[str, str, int]]:
    test_defs: list[tuple[str, str, int]] = []
    for path in sorted(Path("tests").rglob("test_*.py")):
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
