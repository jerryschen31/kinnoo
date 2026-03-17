import subprocess
import sys
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
    assert "Starting import analysis for:" in result.stdout
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
