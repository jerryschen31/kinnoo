from kinnoo.input_guard import (
    InputGuardResult,
    InputWarning,
    get_default_guard,
)


def test_result_models_structure() -> None:
    warning = InputWarning(
        threat_category="SQL_INJECTION",
        description="Possible SQL injection pattern",
        param_name="query",
    )
    assert warning.threat_category == "SQL_INJECTION"
    assert warning.description == "Possible SQL injection pattern"
    assert warning.param_name == "query"

    safe_result = InputGuardResult(safe=True, warnings=[])
    assert safe_result.safe is True
    assert safe_result.warnings == []

    unsafe_result = InputGuardResult(safe=False, warnings=[warning])
    assert unsafe_result.safe is False
    assert len(unsafe_result.warnings) == 1
    assert unsafe_result.warnings[0] == warning


def test_get_default_guard_protocol_contract() -> None:
    guard = get_default_guard()

    assert hasattr(guard, "check")
    assert hasattr(guard, "check_inputs")

    single_result = guard.check("safe text")
    assert isinstance(single_result, InputGuardResult)
    assert single_result.safe is True
    assert single_result.warnings == []

    multi_result = guard.check_inputs([
        ("query", "safe text", "text"),
        ("path", "safe/path.txt", "file_path"),
    ])
    assert isinstance(multi_result, InputGuardResult)
    assert multi_result.safe is True
    assert multi_result.warnings == []
