from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib


def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _read_pyproject() -> dict[str, object]:
    with Path("pyproject.toml").open("rb") as file_handle:
        return tomllib.load(file_handle)


def test_feature99_group1() -> None:
    pyproject = _read_pyproject()
    project = pyproject.get("project")
    assert isinstance(project, dict)

    for required_key in [
        "name",
        "version",
        "description",
        "authors",
        "license",
        "classifiers",
        "urls",
    ]:
        assert required_key in project, f"Missing project metadata key: {required_key}"

    workflow_text = _read_text(".github/workflows/pypi-publish.yml")
    assert "push:" in workflow_text
    assert "branches:" in workflow_text
    assert "- master" in workflow_text
    assert "release:" not in workflow_text

    build_result = subprocess.run(
        [sys.executable, "-m", "build"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert build_result.returncode == 0, build_result.stdout + "\n" + build_result.stderr

    dist_dir = Path("dist")
    wheel_paths = sorted(dist_dir.glob("kinnoo-*.whl"))
    assert wheel_paths, "Expected a wheel in dist/ after build"

    with tempfile.TemporaryDirectory() as install_dir:
        install_result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--target",
                install_dir,
                str(wheel_paths[-1]),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert install_result.returncode == 0, install_result.stdout + "\n" + install_result.stderr

        version_result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from importlib.metadata import version; print(version('kinnoo'))",
            ],
            check=False,
            capture_output=True,
            text=True,
            env={"PYTHONPATH": install_dir},
        )
        assert version_result.returncode == 0, version_result.stdout + "\n" + version_result.stderr
        assert version_result.stdout.strip() == str(project.get("version", "")).strip()


def test_feature99_group2() -> None:
    # Group2 is implemented in task409.
    pass
