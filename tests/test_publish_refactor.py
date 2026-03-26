import os
import subprocess
import sys
import zipfile
from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"


def _write_archive(
    archive_root: Path,
    *,
    name: str,
    version: str,
    run_content: str = "print('ok')\n",
    manifest_override: str | None = None,
) -> Path:
    archive_path = archive_root / name / version / f"{name}.kno"
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_text = manifest_override or (
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


def test_publish_name_resolves_latest_local_archive(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"

    older_archive = _write_archive(
        archive_root,
        name="demo-agent",
        version="1.0.0",
        run_content="print('version-1.0.0')\n",
    )
    latest_archive = _write_archive(
        archive_root,
        name="demo-agent",
        version="2.0.0",
        run_content="print('version-2.0.0')\n",
    )

    env = dict(
        **os.environ,
        KINNOO_ARCHIVE_ROOT=str(archive_root),
        KINNOO_REGISTRY_ROOT=str(registry_root),
    )

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "demo-agent"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert f"Source archive: {latest_archive}" in combined_output

    target_archive = registry_root / "demo-agent" / "2.0.0" / "demo-agent.kno"
    assert target_archive.exists()
    assert f"Target registry path: {target_archive}" in combined_output

    assert target_archive.read_bytes() == latest_archive.read_bytes()
    assert target_archive.read_bytes() != older_archive.read_bytes()


def test_publish_errors_for_missing_or_invalid_archive_source(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    env = dict(
        **os.environ,
        KINNOO_ARCHIVE_ROOT=str(archive_root),
        KINNOO_REGISTRY_ROOT=str(registry_root),
    )

    missing_agent_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "missing-agent"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    missing_agent_output = f"{missing_agent_result.stdout}\n{missing_agent_result.stderr}"
    assert missing_agent_result.returncode != 0
    assert "Local archive source for agent 'missing-agent' was not found" in missing_agent_output

    empty_agent_dir = archive_root / "empty-agent"
    empty_agent_dir.mkdir(parents=True, exist_ok=True)
    no_versions_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "empty-agent"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    no_versions_output = f"{no_versions_result.stdout}\n{no_versions_result.stderr}"
    assert no_versions_result.returncode != 0
    assert "Local archive source for agent 'empty-agent' has no versions." in no_versions_output

    _write_archive(
        archive_root,
        name="broken-agent",
        version="3.0.0",
        manifest_override=(
            "\n".join(
                [
                    "name: broken-agent",
                    "version: not-a-semver",
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
        ),
    )

    invalid_metadata_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "broken-agent"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    invalid_metadata_output = f"{invalid_metadata_result.stdout}\n{invalid_metadata_result.stderr}"
    assert invalid_metadata_result.returncode != 0
    assert "Manifest validation failed for resolved local archive source." in invalid_metadata_output
    assert "version" in invalid_metadata_output


def test_publish_rolls_existing_tagged_to_untagged(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"
    env = dict(
        **os.environ,
        KINNOO_ARCHIVE_ROOT=str(archive_root),
        KINNOO_REGISTRY_ROOT=str(registry_root),
    )

    source_archive_v1 = _write_archive(
        archive_root,
        name="rollover-agent",
        version="1.0.0",
        run_content="print('payload-v1')\n",
    )
    first_publish = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "rollover-agent"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    assert first_publish.returncode == 0

    target_archive = registry_root / "rollover-agent" / "1.0.0" / "rollover-agent.kno"
    assert target_archive.exists()
    published_v1_bytes = target_archive.read_bytes()
    assert published_v1_bytes == source_archive_v1.read_bytes()

    source_archive_v2 = _write_archive(
        archive_root,
        name="rollover-agent",
        version="1.0.0",
        run_content="print('payload-v2')\n",
    )
    second_publish = subprocess.run(
        [sys.executable, str(CLI_PATH), "publish", "rollover-agent"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    combined_output = f"{second_publish.stdout}\n{second_publish.stderr}"
    assert second_publish.returncode == 0
    assert f"Target registry path: {target_archive}" in combined_output

    rollover_archive = registry_root / "rollover-agent" / "untagged-1" / "rollover-agent.kno"
    assert rollover_archive.exists()
    assert rollover_archive.read_bytes() == published_v1_bytes

    assert target_archive.read_bytes() == source_archive_v2.read_bytes()
    assert target_archive.read_bytes() != published_v1_bytes
    assert (
        f"Rollover archived previous tagged artifact to: {rollover_archive}"
        in combined_output
    )


def test_publish_uses_home_absolute_mock_registry_path(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    simulated_home = tmp_path / "simulated-home"
    simulated_home.mkdir(parents=True, exist_ok=True)

    source_archive = _write_archive(
        archive_root,
        name="absolute-path-agent",
        version="1.0.0",
        run_content="print('absolute-path')\n",
    )

    publish_cwd = tmp_path / "publish-cwd"
    publish_cwd.mkdir(parents=True, exist_ok=True)
    cli_path = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"

    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "HOME": str(simulated_home),
    }
    env.pop("KINNOO_REGISTRY_ROOT", None)

    result = subprocess.run(
        [sys.executable, str(cli_path), "publish", "absolute-path-agent"],
        cwd=publish_cwd,
        capture_output=True,
        text=True,
        env=env,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    expected_target = (
        simulated_home
        / "kinnoo-mock-registry-scratch"
        / "jerry"
        / "absolute-path-agent"
        / "1.0.0"
        / "absolute-path-agent.kno"
    )

    assert result.returncode == 0
    assert expected_target.is_absolute()
    assert expected_target.exists()
    assert expected_target.read_bytes() == source_archive.read_bytes()
    assert f"Target registry path: {expected_target}" in combined_output
    assert "Target registry path: registry-scratch/jerry/" not in combined_output
