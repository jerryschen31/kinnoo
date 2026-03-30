from __future__ import annotations

import json
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_TEST_ASSERTION_TYPES: tuple[str, ...] = ("contains", "equals", "regex")


@dataclass(frozen=True)
class DeclarativeAssertion:
    assertion_type: str
    expected_value: str
    target_stream: str = "stdout"


@dataclass(frozen=True)
class DeclarativeTestCase:
    test_id: str
    name: str
    input_text: str
    assertions: tuple[DeclarativeAssertion, ...]
    timeout_seconds: float
    expected_exit_code: int
    tags: tuple[str, ...]


@dataclass(frozen=True)
class TestCaseExecutionResult:
    test_id: str
    name: str
    passed: bool
    runtime_type: str
    actual_exit_code: int
    expected_exit_code: int
    assertions_passed: int
    assertions_total: int
    timed_out: bool
    duration_ms: int
    failure_reason: str


def _normalize_assertion(raw_assertion: Any, path_prefix: str) -> tuple[DeclarativeAssertion | None, list[str]]:
    errors: list[str] = []

    if isinstance(raw_assertion, str):
        value = raw_assertion.strip()
        if not value:
            return None, [f"{path_prefix} must be a non-empty string when shorthand form is used."]
        return DeclarativeAssertion(assertion_type="contains", expected_value=value), errors

    if not isinstance(raw_assertion, dict):
        return None, [f"{path_prefix} must be a string or object assertion."]

    if "type" in raw_assertion or "value" in raw_assertion:
        assertion_type = raw_assertion.get("type")
        assertion_value = raw_assertion.get("value")
        target_stream = raw_assertion.get("target", "stdout")

        if not isinstance(assertion_type, str) or assertion_type not in SUPPORTED_TEST_ASSERTION_TYPES:
            supported = ", ".join(SUPPORTED_TEST_ASSERTION_TYPES)
            errors.append(f"{path_prefix}.type must be one of: {supported}.")
        if not isinstance(assertion_value, str) or not assertion_value.strip():
            errors.append(f"{path_prefix}.value must be a non-empty string.")
        if target_stream not in ("stdout", "stderr"):
            errors.append(f"{path_prefix}.target must be either 'stdout' or 'stderr'.")

        if errors:
            return None, errors
        return (
            DeclarativeAssertion(
                assertion_type=assertion_type,
                expected_value=assertion_value,
                target_stream=target_stream,
            ),
            errors,
        )

    matching_keys = [key for key in SUPPORTED_TEST_ASSERTION_TYPES if key in raw_assertion]
    if len(matching_keys) != 1:
        supported = ", ".join(SUPPORTED_TEST_ASSERTION_TYPES)
        errors.append(f"{path_prefix} object form must include exactly one of: {supported}.")
        return None, errors

    assertion_type = matching_keys[0]
    raw_value = raw_assertion.get(assertion_type)
    if not isinstance(raw_value, str) or not raw_value.strip():
        errors.append(f"{path_prefix}.{assertion_type} must be a non-empty string.")
        return None, errors

    return DeclarativeAssertion(assertion_type=assertion_type, expected_value=raw_value), errors


def validate_kinnoo_tests_document(document: Any, *, prefix: str = "") -> list[str]:
    errors: list[str] = []
    base = f"{prefix}." if prefix else ""

    if not isinstance(document, dict):
        return [f"{prefix or 'tests document'} must be a YAML mapping."]

    version = document.get("version")
    if not isinstance(version, (int, str)):
        errors.append(f"{base}version must be an int or string.")

    tests = document.get("tests")
    if not isinstance(tests, list):
        errors.append(f"{base}tests must be a list.")
        return errors

    for index, test_case in enumerate(tests):
        path = f"{base}tests[{index}]"
        if not isinstance(test_case, dict):
            errors.append(f"{path} must be a mapping.")
            continue

        required_fields = (
            "id",
            "name",
            "input",
            "assertions",
            "timeout_seconds",
            "expected_exit_code",
        )
        for field_name in required_fields:
            if field_name not in test_case:
                errors.append(f"Missing required field: {path}.{field_name}")

        test_id = test_case.get("id")
        if test_id is not None and (not isinstance(test_id, str) or not test_id.strip()):
            errors.append(f"{path}.id must be a non-empty string.")

        test_name = test_case.get("name")
        if test_name is not None and (not isinstance(test_name, str) or not test_name.strip()):
            errors.append(f"{path}.name must be a non-empty string.")

        input_text = test_case.get("input")
        if input_text is not None and not isinstance(input_text, str):
            errors.append(f"{path}.input must be a string.")

        timeout_seconds = test_case.get("timeout_seconds")
        if timeout_seconds is not None:
            if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
                errors.append(f"{path}.timeout_seconds must be a numeric value.")
            elif float(timeout_seconds) <= 0:
                errors.append(f"{path}.timeout_seconds must be greater than zero.")

        expected_exit_code = test_case.get("expected_exit_code")
        if expected_exit_code is not None and (isinstance(expected_exit_code, bool) or not isinstance(expected_exit_code, int)):
            errors.append(f"{path}.expected_exit_code must be an int.")

        tags = test_case.get("tags")
        if tags is not None:
            if not isinstance(tags, list):
                errors.append(f"{path}.tags must be a list of strings.")
            else:
                for tag_index, tag in enumerate(tags):
                    if not isinstance(tag, str) or not tag.strip():
                        errors.append(f"{path}.tags[{tag_index}] must be a non-empty string.")

        assertions = test_case.get("assertions")
        if assertions is None:
            continue
        if not isinstance(assertions, list) or len(assertions) == 0:
            errors.append(f"{path}.assertions must be a non-empty list.")
            continue

        for assertion_index, assertion in enumerate(assertions):
            _, assertion_errors = _normalize_assertion(
                assertion,
                f"{path}.assertions[{assertion_index}]",
            )
            errors.extend(assertion_errors)

    return errors


def _parse_test_cases(document: dict[str, Any]) -> list[DeclarativeTestCase]:
    parsed_tests: list[DeclarativeTestCase] = []
    for test_case in document.get("tests", []):
        assertions: list[DeclarativeAssertion] = []
        for index, raw_assertion in enumerate(test_case["assertions"]):
            parsed, assertion_errors = _normalize_assertion(
                raw_assertion,
                f"tests[{test_case.get('id', '?')}].assertions[{index}]",
            )
            if assertion_errors or parsed is None:
                raise ValueError("Assertion normalization failed after validation.")
            assertions.append(parsed)

        tags = tuple(test_case.get("tags", []))
        parsed_tests.append(
            DeclarativeTestCase(
                test_id=str(test_case["id"]),
                name=str(test_case["name"]),
                input_text=str(test_case["input"]),
                assertions=tuple(assertions),
                timeout_seconds=float(test_case["timeout_seconds"]),
                expected_exit_code=int(test_case["expected_exit_code"]),
                tags=tags,
            )
        )

    return parsed_tests


def _read_yaml_file(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML parse error in {path}: {exc}") from exc


def load_kinnoo_test_cases(agent_dir_arg: str, tests_file_arg: str | None = None) -> tuple[list[DeclarativeTestCase], str]:
    agent_dir = Path(agent_dir_arg)
    if not agent_dir.exists() or not agent_dir.is_dir():
        raise ValueError(f"Agent directory not found: {agent_dir}")

    if tests_file_arg:
        tests_path = Path(tests_file_arg)
        if not tests_path.is_absolute():
            tests_path = agent_dir / tests_path
        if not tests_path.exists():
            raise ValueError(f"Tests file not found: {tests_path}")
        test_doc = _read_yaml_file(tests_path)
        errors = validate_kinnoo_tests_document(test_doc)
        if errors:
            raise ValueError("Invalid tests spec:\n- " + "\n- ".join(errors))
        return _parse_test_cases(test_doc), str(tests_path)

    canonical_tests_path = agent_dir / "kinnoo.tests.yaml"
    if canonical_tests_path.exists():
        test_doc = _read_yaml_file(canonical_tests_path)
        errors = validate_kinnoo_tests_document(test_doc)
        if errors:
            raise ValueError("Invalid tests spec:\n- " + "\n- ".join(errors))
        return _parse_test_cases(test_doc), str(canonical_tests_path)

    manifest_path = agent_dir / "kinnoo.yaml"
    if not manifest_path.exists():
        raise ValueError("No tests declaration found. Expected kinnoo.tests.yaml or kinnoo.yaml with tests/tests_file.")

    manifest_doc = _read_yaml_file(manifest_path)
    if not isinstance(manifest_doc, dict):
        raise ValueError("kinnoo.yaml must be a mapping to resolve tests declarations.")

    tests_file_ref = manifest_doc.get("tests_file")
    if isinstance(tests_file_ref, str) and tests_file_ref.strip():
        linked_path = agent_dir / tests_file_ref
        if not linked_path.exists():
            raise ValueError(f"Manifest tests_file target not found: {linked_path}")
        test_doc = _read_yaml_file(linked_path)
        errors = validate_kinnoo_tests_document(test_doc)
        if errors:
            raise ValueError("Invalid tests spec:\n- " + "\n- ".join(errors))
        return _parse_test_cases(test_doc), str(linked_path)

    inline_tests = manifest_doc.get("tests")
    if inline_tests is not None:
        inline_doc = {
            "version": manifest_doc.get("tests_version", 1),
            "tests": inline_tests,
        }
        errors = validate_kinnoo_tests_document(inline_doc, prefix="kinnoo.yaml")
        if errors:
            raise ValueError("Invalid tests spec:\n- " + "\n- ".join(errors))
        return _parse_test_cases(inline_doc), str(manifest_path)

    raise ValueError("No tests declaration found. Expected kinnoo.tests.yaml or kinnoo.yaml with tests/tests_file.")


def run_test_command(agent_dir_arg: str, tests_file_arg: str | None = None, validate_only: bool = False, json_output: bool = False) -> int:
    try:
        test_cases, tests_source = load_kinnoo_test_cases(agent_dir_arg, tests_file_arg)
    except ValueError as exc:
        print(f"Error: {exc}", flush=True)
        return 1

    if validate_only:
        if json_output:
            print(
                json.dumps(
                    {
                        "valid": True,
                        "source": tests_source,
                        "total": len(test_cases),
                    },
                    sort_keys=True,
                )
            )
        else:
            print(f"[kinnoo test] Valid tests declaration loaded from: {tests_source}")
            print(f"[kinnoo test] Parsed {len(test_cases)} test case(s).")
        return 0

    try:
        manifest = _load_manifest(agent_dir_arg)
    except ValueError as exc:
        print(f"Error: {exc}", flush=True)
        return 1

    runtime = manifest.get("runtime")
    if not isinstance(runtime, dict):
        print("Error: kinnoo.yaml runtime block is required for test execution.", flush=True)
        return 1

    execution_results: list[TestCaseExecutionResult] = []
    for test_case in test_cases:
        execution_results.append(_execute_test_case(Path(agent_dir_arg), manifest, test_case))

    passed_count = sum(1 for result in execution_results if result.passed)
    total_count = len(execution_results)
    failed_count = total_count - passed_count

    if json_output:
        print(
            json.dumps(
                {
                    "source": tests_source,
                    "total": total_count,
                    "passed": passed_count,
                    "failed": failed_count,
                    "results": [
                        {
                            "id": result.test_id,
                            "name": result.name,
                            "status": "passed" if result.passed else "failed",
                            "runtime_type": result.runtime_type,
                            "exit_code": result.actual_exit_code,
                            "expected_exit_code": result.expected_exit_code,
                            "assertions_passed": result.assertions_passed,
                            "assertions_total": result.assertions_total,
                            "timed_out": result.timed_out,
                            "duration_ms": result.duration_ms,
                            "failure_reason": result.failure_reason,
                        }
                        for result in execution_results
                    ],
                },
                sort_keys=True,
            )
        )
    else:
        print(f"[kinnoo test] Loaded {total_count} test case(s) from {tests_source}")
        for result in execution_results:
            label = "PASS" if result.passed else "FAIL"
            summary = (
                f"[{label}] {result.test_id} ({result.runtime_type}) "
                f"assertions {result.assertions_passed}/{result.assertions_total} "
                f"exit {result.actual_exit_code}/{result.expected_exit_code}"
            )
            if result.failure_reason:
                summary += f" reason={result.failure_reason}"
            print(summary)
        print(f"[kinnoo test] Summary: {passed_count}/{total_count} passed")

    return 0 if failed_count == 0 else 1


def _load_manifest(agent_dir_arg: str) -> dict[str, Any]:
    manifest_path = Path(agent_dir_arg) / "kinnoo.yaml"
    if not manifest_path.exists():
        raise ValueError(f"Manifest file not found: {manifest_path}")

    manifest_doc = _read_yaml_file(manifest_path)
    if not isinstance(manifest_doc, dict):
        raise ValueError("kinnoo.yaml must be a mapping.")
    return manifest_doc


def _build_runtime_command(agent_dir: Path, manifest: dict[str, Any], input_text: str) -> tuple[list[str], str]:
    runtime = manifest.get("runtime", {})
    if not isinstance(runtime, dict):
        return [], "unknown"

    runtime_type = str(runtime.get("type", "one-shot"))
    runtime_language = str(runtime.get("language", "python"))
    entrypoint = str(manifest.get("entrypoint", "run.py"))
    runtime_path = str(runtime.get("path", "")).strip()
    run_command = runtime.get("run_command")

    if runtime_type == "daemon" and isinstance(run_command, str) and run_command.strip():
        command = shlex.split(run_command.strip())
        command.append(input_text)
        return command, runtime_type

    if runtime_language == "nodejs":
        executable = runtime_path or "node"
    else:
        executable = runtime_path or "python3"

    command = [executable, entrypoint, input_text]
    return command, runtime_type


def _execute_test_case(agent_dir: Path, manifest: dict[str, Any], test_case: DeclarativeTestCase) -> TestCaseExecutionResult:
    command, runtime_type = _build_runtime_command(agent_dir, manifest, test_case.input_text)
    if not command:
        return TestCaseExecutionResult(
            test_id=test_case.test_id,
            name=test_case.name,
            passed=False,
            runtime_type="unknown",
            actual_exit_code=1,
            expected_exit_code=test_case.expected_exit_code,
            assertions_passed=0,
            assertions_total=len(test_case.assertions),
            timed_out=False,
            duration_ms=0,
            failure_reason="runtime_command_unresolved",
        )

    started_at = time.time()
    timed_out = False
    try:
        result = subprocess.run(
            command,
            cwd=str(agent_dir),
            capture_output=True,
            text=True,
            timeout=test_case.timeout_seconds,
        )
        actual_exit_code = int(result.returncode)
        stdout_text = result.stdout
        stderr_text = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        actual_exit_code = 124
        stdout_text = exc.stdout or ""
        stderr_text = exc.stderr or ""

    assertion_passes = 0
    for assertion in test_case.assertions:
        target_text = stdout_text if assertion.target_stream == "stdout" else stderr_text
        if _assertion_matches(assertion, target_text):
            assertion_passes += 1

    exit_code_match = actual_exit_code == test_case.expected_exit_code
    assertions_match = assertion_passes == len(test_case.assertions)
    passed = (not timed_out) and exit_code_match and assertions_match

    failure_reasons: list[str] = []
    if timed_out:
        failure_reasons.append("timeout")
    if not exit_code_match:
        failure_reasons.append("exit_code_mismatch")
    if not assertions_match:
        failure_reasons.append("assertions_failed")

    duration_ms = int((time.time() - started_at) * 1000)
    return TestCaseExecutionResult(
        test_id=test_case.test_id,
        name=test_case.name,
        passed=passed,
        runtime_type=runtime_type,
        actual_exit_code=actual_exit_code,
        expected_exit_code=test_case.expected_exit_code,
        assertions_passed=assertion_passes,
        assertions_total=len(test_case.assertions),
        timed_out=timed_out,
        duration_ms=duration_ms,
        failure_reason=",".join(failure_reasons),
    )


def _assertion_matches(assertion: DeclarativeAssertion, output_text: str) -> bool:
    if assertion.assertion_type == "contains":
        return assertion.expected_value in output_text
    if assertion.assertion_type == "equals":
        return output_text.strip() == assertion.expected_value.strip()
    if assertion.assertion_type == "regex":
        return re.search(assertion.expected_value, output_text, flags=re.MULTILINE) is not None
    return False
