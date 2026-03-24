# Task256 Notes - Import Requirements Generation Gap and Fix

Date: 2026-03-21

## UAT Gap Assessment

Confirmed: `kinnoo import` previously did not guarantee creation of `requirements.txt`.

Observed impact from task255 UATs:
- `kinnoo inspect` failed for imported LangChain examples due to missing `requirements.txt`.
- `kinnoo pack` failed for imported LangChain examples due to missing `requirements.txt`.

Assessment of prior feature19 tasks:
- `task164` (in-place manifest write/collision/rollback) completed its stated manifest goals, but did not include requirements artifact generation needed for downstream inspect/pack readiness.
- `task165` (analyzer integration/wizard) did not persist inferred dependencies into a generated `requirements.txt` file when missing.
- `task167` (in-place runnability gate) validated run path, but did not gate packaging-readiness expectations requiring `requirements.txt` presence.

Conclusion: these tasks were valid for their original acceptance criteria, but they did not fully satisfy practical import completeness for inspect/pack workflows. This is now addressed by task256.

## Implementation Summary

Updated `kinnoo import` to create missing `requirements.txt` for Python projects:
1. Prefer analyzer-inferred dependencies when available.
2. If inference is empty, attempt `uv export --format requirements-txt --no-hashes`.
3. If export is unavailable/fails, create deterministic empty `requirements.txt` and print actionable guidance.
4. Preserve rollback safety: if import fails after artifact creation, clean up generated files.

UAT follow-up fix (LangChain sample):
5. Analyzer now infers dependencies from known import namespaces when requirements/pyproject are absent (e.g., `langchain_core` -> `langchain-core`).
6. Framework inference now recognizes LangChain imports and prefers `langchain` when both LangChain and OpenAI SDK imports appear in the same project.

## Tests Added

- `tests/test_cli_import.py::test_feature19_import_generates_requirements_via_uv_export`
- `tests/test_cli_import.py::test_feature19_import_generates_empty_requirements_when_detection_unavailable`
- `tests/test_analyzer.py::test_framework_prefers_langchain_when_openai_and_langchain_both_present`
- `tests/test_analyzer.py::test_dependency_inference_uses_known_import_namespaces`
- `tests/test_cli_import.py::test_feature19_import_generates_requirements_from_import_inference`

## Test Runs

Command:
```bash
python3 -m pytest tests/test_cli_import.py -k "requirements_via_uv_export or empty_requirements_when_detection_unavailable" -q
```
Result:
```text
2 passed, 14 deselected
```

Command:
```bash
python3 src/validate_project_manifests.py
```
Result:
```text
Validation passed: manifests are consistent
```

Command:
```bash
python3 -m pytest tests/test_analyzer.py tests/test_cli_import.py -q
```
Result:
```text
31 passed
```

Real-sample verification:
- Imported `/tmp/langchain-openai-assistant-agent-repro` from `example-scratch/agents/langchain-openai-assistant-agent`.
- Generated `kinnoo.yaml` now contains `framework: langchain`.
- Generated `requirements.txt` now contains:
	- `langchain-core`
	- `openai`
