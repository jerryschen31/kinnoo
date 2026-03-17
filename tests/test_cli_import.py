import subprocess
import sys
import os
from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"


def test_feature19_import_defaults_to_current_directory(tmp_path):
    project_dir = tmp_path / "feature19-default-path-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Detected values from analyzer:" in result.stdout
    assert "Usage:" not in result.stderr


def test_feature19_import_invalid_args_show_usage(tmp_path):
    project_dir = tmp_path / "feature19-invalid-args-project"
    project_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir), "extra-arg"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "usage:" in combined
    assert "import" in combined


def test_feature19_import_writes_manifest_in_place(tmp_path):
    project_dir = tmp_path / "feature19-write-in-place-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello from existing project')\n", encoding="utf-8")
    (project_dir / "notes.txt").write_text("keep me unchanged\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Imported project in-place:" in result.stdout
    manifest_path = project_dir / "kinnoo.yaml"
    assert manifest_path.exists()
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "entrypoint: run.py" in manifest_text
    assert "runtime:" in manifest_text
    # Ensure no scaffold-copy behavior: only existing files plus kinnoo.yaml.
    assert not (project_dir / "prompts").exists()
    assert not (project_dir / "tools").exists()
    assert (project_dir / "notes.txt").read_text(encoding="utf-8") == "keep me unchanged\n"


def test_feature19_import_failure_rolls_back_partial_output(tmp_path):
    project_dir = tmp_path / "feature19-rollback-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('rollback project')\n", encoding="utf-8")

    env = dict(os.environ)
    env["KINNOO_IMPORT_FAIL_AFTER_WRITE"] = "1"

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "rolled back partial artifacts" in combined
    assert not (project_dir / "kinnoo.yaml").exists()


def test_feature19_import_collision_requires_explicit_override(tmp_path):
    project_dir = tmp_path / "feature19-collision-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    existing_manifest = (
        "name: existing-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \">=3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )
    manifest_path = project_dir / "kinnoo.yaml"
    manifest_path.write_text(existing_manifest, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "already exists" in combined
    assert "override" in combined
    assert manifest_path.read_text(encoding="utf-8") == existing_manifest


def test_feature19_import_uses_analyzer_inference_and_warnings(tmp_path):
    project_dir = tmp_path / "feature19-analyzer-integration-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "import openai\n"
        "import anthropic\n"
        "import os\n"
        "token = os.getenv('API_TOKEN')\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )
    (project_dir / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\nchatgpt\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined_output = (result.stdout + result.stderr).lower()
    assert "detected values from analyzer" in combined_output
    assert "analyzer warnings" in combined_output
    assert "ambiguous" in combined_output

    manifest_text = (project_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "entrypoint: run.py" in manifest_text
    assert "framework: chatgpt" in manifest_text
    assert "requests==2.31.0" in manifest_text
    assert "api_token" in manifest_text.lower()


def test_feature19_confirm_first_wizard_prompt_minimization(tmp_path):
    project_dir = tmp_path / "feature19-confirm-first-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "import openai\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )
    (project_dir / "requirements.txt").write_text("tomli>=2.0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined_output = result.stdout + result.stderr
    assert "Detected values from analyzer:" in combined_output
    assert "Proceed with detected values?" in combined_output
    assert "Provide value for" not in combined_output
