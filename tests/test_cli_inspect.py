import subprocess
import sys
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
