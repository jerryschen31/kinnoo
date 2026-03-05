import os
import subprocess
import sys
import zipfile
from pathlib import Path


def test_publish_cli_usage_and_local_flag(tmp_path: Path) -> None:
    usage_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish"],
        capture_output=True,
        text=True,
    )

    assert usage_result.returncode != 0
    assert "Usage: kinnoo publish <archive.kno> [--local]" in usage_result.stderr

    archive_path = tmp_path / "demo-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "kinnoo.yaml",
            """
name: demo-agent
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
""",
        )
        archive_zip.writestr("run.py", "print('hello')\n")

    registry_root = tmp_path / "registry-sandbox"
    env = dict(**os.environ, KINNOO_REGISTRY_ROOT=str(registry_root))

    publish_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish", str(archive_path), "--local"],
        capture_output=True,
        text=True,
        env=env,
    )

    assert publish_result.returncode == 0
    assert "Published demo-agent==1.2.3" in publish_result.stdout

    expected_archive = (
        registry_root / "demo-agent" / "1.2.3" / "demo-agent.kno"
    )
    assert expected_archive.exists()


def test_publish_extracts_metadata_and_blocks_duplicate_version(tmp_path: Path) -> None:
    archive_path = tmp_path / "duplicate-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "nested/kinnoo.yaml",
            """
name: duplicate-agent
version: 2.0.0
description: Duplicate publish test fixture
author: SWE Agent
license: MIT
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
""",
        )
        archive_zip.writestr("run.py", "print('hello')\n")

    registry_root = tmp_path / "registry-sandbox"
    env = dict(**os.environ, KINNOO_REGISTRY_ROOT=str(registry_root))

    first_publish = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish", str(archive_path)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert first_publish.returncode == 0
    assert "Published duplicate-agent==2.0.0" in first_publish.stdout

    expected_archive_path = (
        registry_root / "duplicate-agent" / "2.0.0" / "duplicate-agent.kno"
    )
    expected_metadata_path = (
        registry_root / "duplicate-agent" / "2.0.0" / "manifest-metadata.json"
    )
    assert expected_archive_path.exists()
    assert expected_metadata_path.exists()

    duplicate_publish = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "publish", str(archive_path)],
        capture_output=True,
        text=True,
        env=env,
    )

    combined_output = f"{duplicate_publish.stdout}\n{duplicate_publish.stderr}"
    assert duplicate_publish.returncode != 0
    assert "Registry already contains published version 'duplicate-agent==2.0.0'" in combined_output
    assert "Refusing to overwrite" in combined_output


def test_install_selector_parsing_preserves_file_install(tmp_path: Path) -> None:
    archive_path = tmp_path / "installable-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "kinnoo.yaml",
            """
name: installable-agent
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
""",
        )
        archive_zip.writestr("run.py", "print('ok')\n")
        archive_zip.writestr("requirements.txt", "")

    install_target_dir = tmp_path / "installed-from-file"
    file_install_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(install_target_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert file_install_result.returncode == 0
    assert "[kinnoo install] Extracted" in file_install_result.stdout
    assert (install_target_dir / "kinnoo.yaml").exists()

    registry_latest_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", "sample-agent"],
        capture_output=True,
        text=True,
    )
    latest_output = f"{registry_latest_result.stdout}\n{registry_latest_result.stderr}"
    assert registry_latest_result.returncode != 0
    assert "Registry selector installs are not implemented yet" in latest_output
    assert "sample-agent" in latest_output

    registry_exact_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", "sample-agent==1.2.3"],
        capture_output=True,
        text=True,
    )
    exact_output = f"{registry_exact_result.stdout}\n{registry_exact_result.stderr}"
    assert registry_exact_result.returncode != 0
    assert "Registry selector installs are not implemented yet" in exact_output
    assert "sample-agent==1.2.3" in exact_output

    invalid_selector_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", "sample-agent=="],
        capture_output=True,
        text=True,
    )
    invalid_output = f"{invalid_selector_result.stdout}\n{invalid_selector_result.stderr}"
    assert invalid_selector_result.returncode != 0
    assert "Invalid registry selector format" in invalid_output
