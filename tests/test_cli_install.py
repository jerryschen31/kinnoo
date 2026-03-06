import subprocess
import sys
import zipfile
import os
from pathlib import Path

# Test51: kinnoo install usage error

def test_install_missing_archive_prints_usage():
    cli_path = "src/kinnoo/cli.py"
    result = subprocess.run([
        sys.executable, cli_path, "install"
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Usage: kinnoo install <archive-path>" in result.stderr


def _create_valid_archive(tmp_path: Path) -> tuple[Path, Path]:
    archive_path = tmp_path / "test-agent.kno"
    expected_dir = tmp_path / "test-agent"
    manifest = (
        "name: test-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('hello')\n")
    return archive_path, expected_dir


def test_install_delegates_to_install_command(tmp_path):
    cli_source = Path("src/kinnoo/cli.py").read_text()
    install_branch_start = cli_source.find('elif args.command == "install":')
    install_branch_end = cli_source.find('elif args.command == "pack":')
    install_branch = cli_source[install_branch_start:install_branch_end]

    assert "install_command import install_agent" in install_branch
    assert "install_agent(" in install_branch
    assert "extractall(" not in install_branch
    assert "Manifest validation failed" not in install_branch

    archive_path, expected_dir = _create_valid_archive(tmp_path)
    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert expected_dir.exists()
    assert (expected_dir / "kinnoo.yaml").exists()


def _create_archive_with_missing_required_wheel(tmp_path: Path) -> Path:
    agent_dir = tmp_path / "fallback-agent-src"
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: fallback-agent
version: 1.0.0
entrypoint: run.py
runtime:
  type: one-shot
  language: python
  version: "3.10"
dependencies: []
inputs:
  type: string
outputs:
  type: string
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('fallback-ok')\n")
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\n")

    wheels_dir = agent_dir / "wheels"
    wheels_dir.mkdir()
    wheel_build = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "requests==2.31.0",
            "--wheel-dir",
            str(wheels_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert wheel_build.returncode == 0, wheel_build.stderr

    requests_wheels = sorted(wheels_dir.glob("requests-*.whl"))
    assert requests_wheels, "Expected requests wheel to exist before removal"
    requests_wheels[0].unlink()

    archive_path = tmp_path / "fallback-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.write(agent_dir / "kinnoo.yaml", arcname="kinnoo.yaml")
        archive.write(agent_dir / "run.py", arcname="run.py")
        archive.write(agent_dir / "requirements.txt", arcname="requirements.txt")
        for wheel in wheels_dir.glob("*.whl"):
            archive.write(wheel, arcname=f"wheels/{wheel.name}")

    return archive_path


def test_install_falls_back_to_pypi_when_wheel_missing(tmp_path):
    archive_path = _create_archive_with_missing_required_wheel(tmp_path)
    target_dir = tmp_path / "installed-fallback-agent"

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "Expected install to succeed via PyPI fallback when a required wheel is missing. "
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "Missing packaged wheels for dependencies: requests" in result.stderr
    assert "Falling back to PyPI; internet access is required." in result.stderr

    python_exe = target_dir / ".venv" / "bin" / "python"
    if not python_exe.exists():
        python_exe = target_dir / ".venv" / "Scripts" / "python.exe"

    import_check = subprocess.run(
        [str(python_exe), "-c", "import requests; print(requests.__version__)"],
        capture_output=True,
        text=True,
    )
    assert import_check.returncode == 0, import_check.stderr
    assert "2.31.0" in import_check.stdout


def _create_packed_archive_with_complete_transitive_wheels(tmp_path: Path, agent_name: str = "offline-ready-agent") -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: {agent_name}
version: 1.0.0
entrypoint: run.py
runtime:
  type: one-shot
  language: python
  version: "3.10"
dependencies: []
inputs:
  type: string
outputs:
  type: string
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('offline-ready-ok')\n")
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\nhttpx==0.27.0\n")

    archive_root = tmp_path / "archive-root"
    pack_env = dict(os.environ)
    pack_env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    pack_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
        capture_output=True,
        text=True,
        env=pack_env,
    )
    assert pack_result.returncode == 0, (
        "Expected pack to succeed for offline-ready fixture. "
        f"STDOUT:\n{pack_result.stdout}\nSTDERR:\n{pack_result.stderr}"
    )

    archive_path = archive_root / agent_name / "1.0.0" / f"{agent_name}.kno"
    assert archive_path.exists(), (
        "Expected packed archive at canonical archive path. "
        f"STDOUT:\n{pack_result.stdout}\nSTDERR:\n{pack_result.stderr}"
    )

    return archive_path


def test_install_offline_succeeds_with_complete_wheels(tmp_path):
    # [agent] test69 validates AC5: complete bundled wheel sets should install
    # without network fallback when offline mode is explicitly enabled.
    archive_path = _create_packed_archive_with_complete_transitive_wheels(tmp_path)
    target_dir = tmp_path / "installed-offline-ready-agent"

    offline_env = dict(os.environ)
    offline_env["PIP_NO_INDEX"] = "1"
    offline_env["KINNOO_OFFLINE"] = "1"

    install_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir)],
        capture_output=True,
        text=True,
        env=offline_env,
    )
    assert install_result.returncode == 0, (
        "Expected offline install to succeed with complete wheels. "
        f"STDOUT:\n{install_result.stdout}\nSTDERR:\n{install_result.stderr}"
    )
    assert "Falling back to PyPI" not in install_result.stderr

    python_exe = target_dir / ".venv" / "bin" / "python"
    if not python_exe.exists():
        python_exe = target_dir / ".venv" / "Scripts" / "python.exe"

    dependency_check = subprocess.run(
        [str(python_exe), "-c", "import requests, httpx; print('ok')"],
        capture_output=True,
        text=True,
    )
    assert dependency_check.returncode == 0, dependency_check.stderr
    assert dependency_check.stdout.strip() == "ok"
