import subprocess
import sys
import zipfile
from pathlib import Path


def _create_agent_with_pinned_transitive_requirements(tmp_path: Path, agent_name: str = "robust-agent") -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: robust-agent
version: 1.0.0
entrypoint: run.py
runtime:
  language: python
  version: '>=3.10'
  type: one-shot
dependencies: []
inputs:
  type: text
outputs:
  type: text
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('ok')\n")
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\nhttpx==0.27.0\n")

    return agent_dir


def _collect_wheel_distribution_names(kno_path: Path) -> set[str]:
    distributions: set[str] = set()
    with zipfile.ZipFile(kno_path, "r") as archive:
        for name in archive.namelist():
            if not name.startswith("wheels/") or not name.endswith(".whl"):
                continue
            wheel_filename = Path(name).name
            distribution = wheel_filename.split("-", 1)[0].lower()
            distributions.add(distribution)
    return distributions


def test_pack_includes_transitive_wheels_for_pinned_deps(tmp_path):
    # [agent] test65 should be run for packaging changes that might impact dependency
    # closure behavior (resolver flags, wheel build strategy, or archive assembly).
    agent_dir = _create_agent_with_pinned_transitive_requirements(tmp_path)

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"kinnoo pack failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"

    kno_path = tmp_path / f"{agent_dir.name}.kno"
    assert kno_path.exists(), "Expected .kno archive to be created"

    distributions = _collect_wheel_distribution_names(kno_path)

    expected_subset = {
        "requests",   # direct
        "httpx",      # direct
        "urllib3",    # transitive via requests
        "certifi",    # transitive via requests/httpx
        "httpcore",   # transitive via httpx
        "anyio",      # transitive via httpcore
    }

    missing = expected_subset - distributions
    assert not missing, (
        "Expected direct + transitive dependency wheels in archive. "
        f"Missing: {sorted(missing)}. Found: {sorted(distributions)}"
    )
