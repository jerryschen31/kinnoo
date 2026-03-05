import os
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


def test_inspect_shows_env_var_names_not_values(tmp_path: Path) -> None:
        agent_dir = tmp_path / "env-var-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "kinnoo.yaml").write_text(
                """
name: env-var-agent
version: 1.0.0
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
env_vars:
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
""",
                encoding="utf-8",
        )

        env = os.environ.copy()
        env.update(
            {
                "OPENAI_API_KEY": "sk-openai-secret-value",
                "ANTHROPIC_API_KEY": "sk-anthropic-secret-value",
            }
        )

        result = subprocess.run(
                [sys.executable, "src/kinnoo/cli.py", "inspect", str(agent_dir)],
                capture_output=True,
                text=True,
                env=env,
        )

        combined_output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0
        assert "- Env Vars:" in result.stdout
        assert "  - OPENAI_API_KEY" in result.stdout
        assert "  - ANTHROPIC_API_KEY" in result.stdout
        assert "sk-openai-secret-value" not in combined_output
        assert "sk-anthropic-secret-value" not in combined_output

def test_missing_manifest_guidance_uses_centralized_template_with_agent_note(tmp_path: Path) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        templates_path = repo_root / "src" / "kinnoo" / "templates.py"
        inspect_path = repo_root / "src" / "kinnoo" / "inspect_command.py"

        templates_text = templates_path.read_text(encoding="utf-8")
        inspect_text = inspect_path.read_text(encoding="utf-8")

        assert "INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE" in templates_text
        assert "[agent]" in templates_text
        assert "INSPECT_MINIMAL_KINNOO_YAML_EXAMPLE" in inspect_text
        assert "name: my-agent" not in inspect_text

        missing_manifest_dir = tmp_path / "missing-manifest-centralized"
        missing_manifest_dir.mkdir(parents=True, exist_ok=True)
        (missing_manifest_dir / "requirements.txt").write_text("", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "src/kinnoo/cli.py", "inspect", str(missing_manifest_dir)],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "Minimal example:" in result.stdout
        assert "name: my-agent" in result.stdout
        assert "version: 0.1.0" in result.stdout
        assert "entrypoint: run.py" in result.stdout
        assert "runtime:" in result.stdout
        assert "dependencies: []" in result.stdout
