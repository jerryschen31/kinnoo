import subprocess
import sys
from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"


def _create_agent_fixture(agent_dir: Path, *, with_manifest: bool = True) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)

    if with_manifest:
        (agent_dir / "kinnoo.yaml").write_text(
            "\n".join(
                [
                    "name: preflight-agent",
                    "version: 1.0.0",
                    "entrypoint: run.py",
                    "runtime:",
                    "  language: python",
                    "  version: \">=3.10\"",
                    "  type: one-shot",
                    "dependencies: []",
                    "inputs:",
                    "  type: text",
                    "outputs:",
                    "  type: text",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    (agent_dir / "run.py").write_text(
        "from pathlib import Path\n"
        "Path('entrypoint-executed.flag').write_text('executed', encoding='utf-8')\n"
        "print('entrypoint-ran')\n",
        encoding="utf-8",
    )


def test_preflight_runs_checks_without_entrypoint_execution(tmp_path: Path) -> None:
    passing_agent = tmp_path / "preflight-pass-agent"
    _create_agent_fixture(passing_agent, with_manifest=True)

    pass_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(passing_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    pass_output = f"{pass_result.stdout}\n{pass_result.stderr}"

    assert pass_result.returncode == 0
    assert "Preflight checklist:" in pass_output
    assert "[PASS] entrypoint execution path skipped in preflight mode" in pass_output
    assert "Preflight result: PASS" in pass_output
    assert not (tmp_path / "entrypoint-executed.flag").exists()

    failing_agent = tmp_path / "preflight-fail-agent"
    _create_agent_fixture(failing_agent, with_manifest=False)

    fail_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(failing_agent), "--preflight"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    fail_output = f"{fail_result.stdout}\n{fail_result.stderr}"

    assert fail_result.returncode != 0
    assert "Preflight checklist:" in fail_output
    assert "[FAIL] manifest exists" in fail_output
    assert "Preflight result: FAIL" in fail_output
    assert not (tmp_path / "entrypoint-executed.flag").exists()
