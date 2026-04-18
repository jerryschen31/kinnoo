import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"


def _write_archive(
    archive_root: Path,
    *,
    name: str,
    version: str,
    run_content: str,
) -> Path:
    archive_path = archive_root / name / version / f"{name}.kno"
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_text = (
        "\n".join(
            [
                f"name: {name}",
                f"version: {version}",
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
        + "\n"
    )

    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr("kinnoo.yaml", manifest_text)
        archive_zip.writestr("run.py", run_content)
        archive_zip.writestr("requirements.txt", "")

    return archive_path


def _write_archive_at_path(
    archive_path: Path,
    *,
    name: str,
    version: str,
    run_content: str,
) -> Path:
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_text = (
        "\n".join(
            [
                f"name: {name}",
                f"version: {version}",
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
        + "\n"
    )

    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr("kinnoo.yaml", manifest_text)
        archive_zip.writestr("run.py", run_content)
        archive_zip.writestr("requirements.txt", "")

    return archive_path


def _publish_from_local_archive(
    *,
    agent_name: str,
    archive_root: Path,
    registry_root: Path,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
    }
    return subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", agent_name],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def test_install_name_resolves_latest_from_mock_registry(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"

    _write_archive(
        archive_root,
        name="install-agent",
        version="1.0.0",
        run_content="import sys\nprint('install-agent-v1:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )
    _write_archive(
        archive_root,
        name="install-agent",
        version="2.0.0",
        run_content="import sys\nprint('install-agent-v2:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )

    publish_result = _publish_from_local_archive(
        agent_name="install-agent",
        archive_root=archive_root,
        registry_root=registry_root,
        cwd=tmp_path,
    )
    assert publish_result.returncode == 0

    env = {
        **os.environ,
        "KINNOO_REGISTRY_ROOT": str(registry_root),
    }

    install_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "install", "install-agent", "--yes"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    combined_install_output = f"{install_result.stdout}\n{install_result.stderr}"
    assert install_result.returncode == 0
    assert "Resolved registry selector 'install-agent'" in combined_install_output
    assert "install-agent/2.0.0/install-agent.kno" in combined_install_output

    run_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "run",
            str(tmp_path / "install-agent"),
            "hello",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    run_output = f"{run_result.stdout}\n{run_result.stderr}"
    assert run_result.returncode == 0
    assert "install-agent-v2:hello" in run_output

    install_command_source = (Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "install_command.py").read_text(
        encoding="utf-8"
    )
    assert "MockFilesystemRegistryBackend" in install_command_source


def test_install_name_equals_version_from_mock_registry(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"

    _write_archive(
        archive_root,
        name="versioned-install",
        version="1.0.0",
        run_content="import sys\nprint('versioned-install-v1:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )
    _write_archive(
        archive_root,
        name="versioned-install",
        version="2.0.0",
        run_content="import sys\nprint('versioned-install-v2:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )

    publish_latest = _publish_from_local_archive(
        agent_name="versioned-install",
        archive_root=archive_root,
        registry_root=registry_root,
        cwd=tmp_path,
    )
    assert publish_latest.returncode == 0

    shutil.rmtree(archive_root / "versioned-install" / "2.0.0")

    _write_archive(
        archive_root,
        name="versioned-install",
        version="1.0.0",
        run_content="import sys\nprint('versioned-install-v1-refresh:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )
    publish_exact = _publish_from_local_archive(
        agent_name="versioned-install",
        archive_root=archive_root,
        registry_root=registry_root,
        cwd=tmp_path,
    )
    assert publish_exact.returncode == 0

    env = {
        **os.environ,
        "KINNOO_REGISTRY_ROOT": str(registry_root),
    }

    install_exact = subprocess.run(
        [sys.executable, str(CLI_PATH), "install", "versioned-install==1.0.0", "--yes"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    install_exact_output = f"{install_exact.stdout}\n{install_exact.stderr}"
    assert install_exact.returncode == 0
    assert "Resolved registry selector 'versioned-install==1.0.0'" in install_exact_output
    assert "versioned-install/1.0.0/versioned-install.kno" in install_exact_output

    run_exact = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "run",
            str(tmp_path / "versioned-install-1.0.0"),
            "hello",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    run_exact_output = f"{run_exact.stdout}\n{run_exact.stderr}"
    assert run_exact.returncode == 0
    assert "versioned-install-v1-refresh:hello" in run_exact_output

    missing_exact = subprocess.run(
        [sys.executable, str(CLI_PATH), "install", "versioned-install==9.9.9"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    missing_exact_output = f"{missing_exact.stdout}\n{missing_exact.stderr}"
    assert missing_exact.returncode != 0
    assert "Registry version 'versioned-install==9.9.9' was not found." in missing_exact_output


def test_install_file_path_mode_preserved(tmp_path: Path) -> None:
    registry_root = tmp_path / "registry-sandbox"

    archive_path = _write_archive_at_path(
        tmp_path / "file-path-install.kno",
        name="file-path-install",
        version="1.0.0",
        run_content="import sys\nprint('from-file-path:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )

    _write_archive(
        registry_root,
        name="file-path-install",
        version="9.9.9",
        run_content="import sys\nprint('from-registry:' + (sys.argv[1] if len(sys.argv) > 1 else ''))\n",
    )

    env = {
        **os.environ,
        "KINNOO_REGISTRY_ROOT": str(registry_root),
    }

    install_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "install", "file-path-install.kno", "--yes"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    install_output = f"{install_result.stdout}\n{install_result.stderr}"

    assert install_result.returncode == 0
    assert "Resolved registry selector" not in install_output
    assert "Extracted 'file-path-install.kno'" in install_output

    installed_dir = archive_path.with_suffix("")
    assert installed_dir.exists()

    run_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "run",
            str(installed_dir),
            "hello",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    run_output = f"{run_result.stdout}\n{run_result.stderr}"

    assert run_result.returncode == 0
    assert "from-file-path:hello" in run_output
    assert "from-registry" not in run_output
