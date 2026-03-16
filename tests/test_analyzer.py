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


def test_feature27_detect_entrypoint_runtime_framework_with_uncertainty(tmp_path: Path) -> None:
    """test244: detectors infer clear layouts and downgrade confidence for ambiguous ones."""
    clear_project = tmp_path / "feature27-clear-layout"
    clear_project.mkdir(parents=True, exist_ok=True)
    (clear_project / "run.py").write_text(
        "import openai\n"
        "RUNTIME_PORT = 8765\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )
    (clear_project / "pyproject.toml").write_text(
        "[project]\n"
        "name = 'clear-layout'\n"
        "requires-python = '>=3.11'\n",
        encoding="utf-8",
    )

    clear_payload = analyze_project(clear_project).as_dict()
    assert clear_payload["inferred"]["entrypoint"] == "run.py"
    assert clear_payload["inferred"]["runtime"]["language"] == "python"
    assert clear_payload["inferred"]["runtime"]["type"] == "one-shot"
    assert clear_payload["inferred"]["runtime"]["version"] == ">=3.11"
    assert clear_payload["inferred"]["runtime"]["port"] == 8765
    assert clear_payload["inferred"]["framework"] == "chatgpt"
    assert clear_payload["confidence"]["entrypoint"]["score"] >= 0.9
    assert clear_payload["confidence"]["runtime"]["score"] >= 0.8
    assert clear_payload["confidence"]["framework"]["score"] >= 0.8

    ambiguous_project = tmp_path / "feature27-ambiguous-layout"
    ambiguous_project.mkdir(parents=True, exist_ok=True)
    (ambiguous_project / "app.py").write_text(
        "import openai\n"
        "if __name__ == '__main__':\n"
        "    print('app')\n",
        encoding="utf-8",
    )
    (ambiguous_project / "worker.py").write_text(
        "import anthropic\n"
        "if __name__ == '__main__':\n"
        "    print('worker')\n",
        encoding="utf-8",
    )

    ambiguous_payload = analyze_project(ambiguous_project).as_dict()
    assert ambiguous_payload["inferred"]["entrypoint"] is None
    assert ambiguous_payload["inferred"]["framework"] is None
    assert ambiguous_payload["confidence"]["entrypoint"]["score"] < 0.5
    assert ambiguous_payload["confidence"]["runtime"]["score"] < 0.6
    assert ambiguous_payload["confidence"]["framework"]["score"] < 0.5
    warning_text = " ".join(ambiguous_payload["warnings"]).lower()
    assert "ambiguous" in warning_text
