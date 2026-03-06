import json
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
    description: str,
) -> Path:
    archive_path = archive_root / name / version / f"{name}.kno"
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_text = (
        "\n".join(
            [
                f"name: {name}",
                f"version: {version}",
                f"description: {description}",
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
        archive_zip.writestr("run.py", "print('hello')\n")
        archive_zip.writestr("requirements.txt", "")

    return archive_path


def _write_remote_registry_entry(
    registry_root: Path,
    *,
    name: str,
    version: str,
    description: str,
) -> None:
    version_dir = registry_root / name / version
    version_dir.mkdir(parents=True, exist_ok=True)

    archive_path = version_dir / f"{name}.kno"
    with zipfile.ZipFile(archive_path, "w") as archive_zip:
        archive_zip.writestr(
            "kinnoo.yaml",
            "\n".join(
                [
                    f"name: {name}",
                    f"version: {version}",
                    f"description: {description}",
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
        )
        archive_zip.writestr("run.py", "print('remote')\n")
        archive_zip.writestr("requirements.txt", "")

    metadata_path = version_dir / "manifest-metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "name": name,
                "version": version,
                "description": description,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_list_default_local_and_remote_modes(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"

    _write_archive(
        archive_root,
        name="alpha-agent",
        version="1.0.0",
        description="Alpha initial",
    )
    _write_archive(
        archive_root,
        name="alpha-agent",
        version="2.0.0",
        description="Alpha latest",
    )
    _write_archive(
        archive_root,
        name="beta-agent",
        version="0.5.0",
        description="Beta archive",
    )

    _write_remote_registry_entry(
        registry_root,
        name="remote-agent",
        version="9.0.0",
        description="Remote inventory",
    )

    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
    }

    default_local = subprocess.run(
        [sys.executable, str(CLI_PATH), "list"],
        capture_output=True,
        text=True,
        env=env,
    )
    local_flag = subprocess.run(
        [sys.executable, str(CLI_PATH), "list", "--local"],
        capture_output=True,
        text=True,
        env=env,
    )
    remote_flag = subprocess.run(
        [sys.executable, str(CLI_PATH), "list", "--remote"],
        capture_output=True,
        text=True,
        env=env,
    )

    default_output = f"{default_local.stdout}\n{default_local.stderr}"
    local_output = f"{local_flag.stdout}\n{local_flag.stderr}"
    remote_output = f"{remote_flag.stdout}\n{remote_flag.stderr}"

    assert default_local.returncode == 0
    assert local_flag.returncode == 0
    assert remote_flag.returncode == 0

    assert "Local archive agents:" in default_output
    assert "alpha-agent | latest: 2.0.0 | description: Alpha latest" in default_output
    assert "beta-agent | latest: 0.5.0 | description: Beta archive" in default_output
    assert "remote-agent" not in default_output

    assert default_output == local_output

    assert "Remote registry agents:" in remote_output
    assert "remote-agent | latest: 9.0.0 | description: Remote inventory" in remote_output
    assert "alpha-agent" not in remote_output


def test_search_default_local_and_remote_modes(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"

    _write_archive(
        archive_root,
        name="alpha-agent",
        version="1.2.0",
        description="Alpha ARCHIVE entry",
    )
    _write_archive(
        archive_root,
        name="beta-agent",
        version="2.0.0",
        description="Different local description",
    )

    _write_remote_registry_entry(
        registry_root,
        name="remote-alpha",
        version="3.0.0",
        description="alpha in remote metadata",
    )
    _write_remote_registry_entry(
        registry_root,
        name="remote-beta",
        version="4.0.0",
        description="no local match",
    )

    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
    }

    default_local = subprocess.run(
        [sys.executable, str(CLI_PATH), "search", "ALPHA"],
        capture_output=True,
        text=True,
        env=env,
    )
    local_flag = subprocess.run(
        [sys.executable, str(CLI_PATH), "search", "--local", "ALPHA"],
        capture_output=True,
        text=True,
        env=env,
    )
    remote_flag = subprocess.run(
        [sys.executable, str(CLI_PATH), "search", "--remote", "ALPHA"],
        capture_output=True,
        text=True,
        env=env,
    )

    default_output = f"{default_local.stdout}\n{default_local.stderr}"
    local_output = f"{local_flag.stdout}\n{local_flag.stderr}"
    remote_output = f"{remote_flag.stdout}\n{remote_flag.stderr}"

    assert default_local.returncode == 0
    assert local_flag.returncode == 0
    assert remote_flag.returncode == 0

    assert "Local archive search results for: ALPHA" in default_output
    assert "alpha-agent | latest: 1.2.0 | description: Alpha ARCHIVE entry" in default_output
    assert "beta-agent" not in default_output
    assert "remote-alpha" not in default_output

    assert default_output == local_output

    assert "Remote registry search results for: ALPHA" in remote_output
    assert "remote-alpha | latest: 3.0.0 | description: alpha in remote metadata" in remote_output
    assert "remote-beta" not in remote_output
    assert "alpha-agent" not in remote_output
