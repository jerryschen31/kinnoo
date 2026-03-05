import subprocess
import sys
import zipfile
from pathlib import Path


def test_inspect_missing_target_prints_usage() -> None:
    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Usage: kinnoo inspect <target>" in result.stderr


def test_inspect_missing_required_files_prints_guidance(tmp_path: Path) -> None:
        missing_manifest_dir = tmp_path / "missing-manifest"
        missing_manifest_dir.mkdir(parents=True, exist_ok=True)
        (missing_manifest_dir / "requirements.txt").write_text("", encoding="utf-8")

        result_manifest = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "inspect", str(missing_manifest_dir)],
                capture_output=True,
                text=True,
        )

        assert result_manifest.returncode != 0
        assert "kinnoo.yaml" in result_manifest.stdout
        assert "Minimal example:" in result_manifest.stdout
        assert "Traceback" not in result_manifest.stdout
        assert "Traceback" not in result_manifest.stderr

        missing_requirements_dir = tmp_path / "missing-requirements"
        missing_requirements_dir.mkdir(parents=True, exist_ok=True)
        (missing_requirements_dir / "kinnoo.yaml").write_text(
                """
name: test-agent
version: 0.1.0
entrypoint: run.py
runtime:
    language: python
    version: \">=3.10\"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
                encoding="utf-8",
        )

        result_requirements = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "inspect", str(missing_requirements_dir)],
                capture_output=True,
                text=True,
        )

        assert result_requirements.returncode != 0
        assert "requirements.txt" in result_requirements.stdout
        assert "pip install uv" in result_requirements.stdout
        assert "uv export --format requirements-txt > requirements.txt" in result_requirements.stdout
        assert "Traceback" not in result_requirements.stdout
        assert "Traceback" not in result_requirements.stderr


def test_inspect_reads_manifest_from_archive_without_extracting(tmp_path: Path) -> None:
        archive_path = tmp_path / "archive-agent.kno"
        manifest_content = """
name: archive-agent
version: 1.2.3
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies: []
inputs:
    type: text
outputs:
    type: text
"""

        with zipfile.ZipFile(archive_path, "w") as archive_zip:
                archive_zip.writestr("kinnoo.yaml", manifest_content)
                archive_zip.writestr("run.py", "print('hello')\n")

        before_children = {path.name for path in tmp_path.iterdir()}

        result = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "inspect", str(archive_path)],
                capture_output=True,
                text=True,
        )

        after_children = {path.name for path in tmp_path.iterdir()}

        assert result.returncode == 0
        assert "Inspect target type: archive (.kno)" in result.stdout
        assert "Manifest metadata:" in result.stdout
        assert "- Name: archive-agent" in result.stdout
        assert "- Version: 1.2.3" in result.stdout
        assert before_children == after_children
        assert (tmp_path / "archive-agent").exists() is False


def test_inspect_formatting_optional_omission_and_missing_required_field_errors(tmp_path: Path) -> None:
        valid_dir = tmp_path / "valid-inspect-agent"
        valid_dir.mkdir(parents=True, exist_ok=True)
        (valid_dir / "requirements.txt").write_text("", encoding="utf-8")
        (valid_dir / "kinnoo.yaml").write_text(
                """
name: readable-agent
version: 1.0.0
entrypoint: run.py
runtime:
    language: python
    version: ">=3.10"
    type: one-shot
dependencies:
    - requests
inputs:
    type: text
outputs:
    type: text
""",
                encoding="utf-8",
        )

        valid_result = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "inspect", str(valid_dir)],
                capture_output=True,
                text=True,
        )

        assert valid_result.returncode == 0
        assert "Manifest metadata:" in valid_result.stdout
        assert "- Name: readable-agent" in valid_result.stdout
        assert "- Version: 1.0.0" in valid_result.stdout
        assert "- Runtime Type: one-shot" in valid_result.stdout
        assert "- Dependencies:" in valid_result.stdout
        assert "  - requests" in valid_result.stdout
        assert "Description:" not in valid_result.stdout
        assert "Author:" not in valid_result.stdout
        assert "License:" not in valid_result.stdout
        assert "{" not in valid_result.stdout

        invalid_dir = tmp_path / "invalid-inspect-agent"
        invalid_dir.mkdir(parents=True, exist_ok=True)
        (invalid_dir / "requirements.txt").write_text("", encoding="utf-8")
        (invalid_dir / "kinnoo.yaml").write_text(
                """
name: invalid-agent
version: 1.0.0
runtime:
    language: python
    version: ">=3.10"
dependencies: []
inputs:
    type: text
outputs:
    type: text
""",
                encoding="utf-8",
        )

        invalid_result = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "inspect", str(invalid_dir)],
                capture_output=True,
                text=True,
        )

        assert invalid_result.returncode != 0
        assert "Error: Manifest validation failed." in invalid_result.stderr
        assert "Missing required field: 'entrypoint'" in invalid_result.stderr
        assert "Missing required field: 'runtime.type'" in invalid_result.stderr
