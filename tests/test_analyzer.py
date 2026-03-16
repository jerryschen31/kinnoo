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


def test_feature27_detect_dependencies_from_requirements_and_pyproject(tmp_path: Path) -> None:
    """test245: dependency detector merges requirements and pyproject with normalization/dedup."""
    project_dir = tmp_path / "feature27-dependency-layout"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "requirements.txt").write_text(
        "requests>=2.31\n"
        "PyYAML==6.0\n"
        "# comment line\n"
        "\n",
        encoding="utf-8",
    )
    (project_dir / "pyproject.toml").write_text(
        "[project]\n"
        "name = 'dep-layout'\n"
        "dependencies = ['requests>=2.30', 'tomli>=2.0']\n"
        "\n"
        "[project.optional-dependencies]\n"
        "dev = ['pytest>=8.0']\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    dependencies = payload["inferred"]["dependencies"]

    assert "requests>=2.30" in dependencies or "requests>=2.31" in dependencies
    assert "pyyaml==6.0" in dependencies
    assert "tomli>=2.0" in dependencies
    assert "pytest>=8.0" in dependencies
    assert dependencies == sorted(set(dependencies))
    assert payload["confidence"]["dependencies"]["score"] >= 0.8


def test_feature27_detect_env_vars_patterns_and_dedup(tmp_path: Path) -> None:
    """test246: env var detector handles getenv/environ access and deduplicates names."""
    project_dir = tmp_path / "feature27-env-layout"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "run.py").write_text(
        "import os\n"
        "token = os.getenv('API_TOKEN')\n"
        "key = os.environ['OPENAI_API_KEY']\n"
        "region = os.environ.get('AWS_REGION')\n"
        "token_again = os.getenv('API_TOKEN', '')\n",
        encoding="utf-8",
    )
    (project_dir / "worker.py").write_text(
        "import os\n"
        "project = os.environ.get('GOOGLE_CLOUD_PROJECT')\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    env_vars = payload["inferred"]["env_vars"]

    assert env_vars == sorted(env_vars)
    assert env_vars == [
        "API_TOKEN",
        "AWS_REGION",
        "GOOGLE_CLOUD_PROJECT",
        "OPENAI_API_KEY",
    ]
    assert payload["confidence"]["env_vars"]["score"] >= 0.8


def test_feature27_detect_assets_with_path_safety_filter(tmp_path: Path) -> None:
    """test247: asset detector infers safe model/data candidates and filters unsafe path literals."""
    project_dir = tmp_path / "feature27-assets-layout"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "models").mkdir()
    (project_dir / "data").mkdir()
    (project_dir / "models" / "model.onnx").write_text("binary-placeholder", encoding="utf-8")
    (project_dir / "data" / "train.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    (project_dir / "run.py").write_text(
        "MODEL_PATH = 'models/model.onnx'\n"
        "SAFE_DATA = 'data/train.csv'\n"
        "UNSAFE = '../secrets/api-key.txt'\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    assets = payload["inferred"]["assets"]

    assert "models" in assets
    assert "data" in assets
    assert "models/model.onnx" in assets
    assert "data/train.csv" in assets
    assert all(".." not in asset for asset in assets)
    warning_text = " ".join(payload["warnings"]).lower()
    assert "unsafe asset path" in warning_text
    assert payload["confidence"]["assets"]["score"] >= 0.7


def test_feature27_detect_services_with_health_check_hints(tmp_path: Path) -> None:
    """test248: service detector infers endpoints with actionable health-check hints."""
    project_dir = tmp_path / "feature27-services-layout"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "run.py").write_text(
        "REDIS_URL = 'redis://localhost:6379/0'\n"
        "DB_DSN = 'postgresql://user:pass@db.local:5432/app'\n"
        "HEALTH_URL = 'https://api.example.com/health'\n"
        "STATUS_URL = 'https://api.example.com/v1/status'\n",
        encoding="utf-8",
    )

    payload = analyze_project(project_dir).as_dict()
    services = payload["inferred"]["services"]

    def find_service(service_type: str, endpoint_prefix: str) -> dict[str, object]:
        return next(
            service
            for service in services
            if service["type"] == service_type and str(service["endpoint"]).startswith(endpoint_prefix)
        )

    redis_service = find_service("redis", "redis://")
    postgres_service = find_service("postgres", "postgresql://")
    health_service = find_service("http", "https://api.example.com/health")
    status_service = find_service("http", "https://api.example.com/v1/status")

    assert redis_service["health_check_hint"] == "PING"
    assert postgres_service["health_check_hint"] == "SELECT 1"
    assert health_service["health_check_hint"] == "GET /health"
    assert "health_check_hint" not in status_service
    assert payload["confidence"]["services"]["score"] >= 0.7
