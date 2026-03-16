from pathlib import Path

from kinnoo.analyzer import AnalysisReport, analyze_project


def _create_minimal_project_fixture(base_dir: Path) -> Path:
    project_dir = base_dir / "feature27-minimal-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")
    return project_dir


def _feature19_style_adapter(project_dir: Path) -> dict[str, object]:
    # Adapter intentionally consumes analyzer output contract directly and stays
    # free from detector duplication or CLI coupling.
    report = analyze_project(project_dir)
    return report.as_dict()


def test_feature27_analyzer_public_api_and_detector_hooks(tmp_path: Path) -> None:
    """test243: analyzer API is importable and returns detector-oriented report sections."""
    project_dir = _create_minimal_project_fixture(tmp_path)
    report = analyze_project(project_dir)

    assert isinstance(report, AnalysisReport)
    payload = report.as_dict()

    assert set(payload.keys()) == {"inferred", "confidence", "warnings"}

    expected_detector_fields = {
        "entrypoint",
        "runtime",
        "framework",
        "dependencies",
        "env_vars",
        "assets",
        "services",
    }
    assert set(payload["inferred"].keys()) == expected_detector_fields
    assert set(payload["confidence"].keys()) == expected_detector_fields


def test_feature27_report_sections_are_stable(tmp_path: Path) -> None:
    """test249: report schema keeps stable inferred/confidence/warnings sections."""
    project_dir = _create_minimal_project_fixture(tmp_path)
    payload = analyze_project(project_dir).as_dict()

    assert isinstance(payload["inferred"], dict)
    assert isinstance(payload["confidence"], dict)
    assert isinstance(payload["warnings"], list)

    for field_name, metadata in payload["confidence"].items():
        assert isinstance(metadata, dict), f"confidence metadata for {field_name} must be a dict"
        assert "score" in metadata
        assert "evidence" in metadata
        assert isinstance(metadata["score"], float)
        assert isinstance(metadata["evidence"], str)


def test_feature27_analyzer_reusable_for_feature19_import_flow(tmp_path: Path) -> None:
    """test250: analyzer can be consumed through a non-CLI adapter path."""
    project_dir = _create_minimal_project_fixture(tmp_path)
    adapter_payload = _feature19_style_adapter(project_dir)

    assert set(adapter_payload.keys()) == {"inferred", "confidence", "warnings"}
    assert "entrypoint" in adapter_payload["inferred"]
    assert "runtime" in adapter_payload["inferred"]
