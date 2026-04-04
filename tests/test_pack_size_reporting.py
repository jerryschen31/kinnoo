import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path


def _create_agent_for_pack(agent_dir: Path, *, name: str, version: str, with_blob: bool) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)

    files_block = "\nfiles:\n  - blob.bin" if with_blob else ""
    (agent_dir / "kinnoo.yaml").write_text(
        (
            f"name: {name}\n"
            f"version: {version}\n"
            "entrypoint: run.py\n"
            "runtime:\n"
            "  language: python\n"
            "  version: '>=3.10'\n"
            "  type: one-shot\n"
            "dependencies: []\n"
            f"{files_block}\n"
            "inputs:\n"
            "  type: text\n"
            "outputs:\n"
            "  type: text\n"
        ),
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('pack-size')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    if with_blob:
        # Random bytes are intentionally incompressible so archive size stays above warning threshold.
        (agent_dir / "blob.bin").write_bytes(os.urandom(1200 * 1024))


def _write_archive_summary_fixture(
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
        archive_zip.writestr("run.py", "print('list-size')\n")
        archive_zip.writestr("requirements.txt", "")

    return archive_path


def _write_remote_summary_fixture(
    registry_root: Path,
    *,
    name: str,
    version: str,
    description: str,
) -> Path:
    archive_path = registry_root / name / version / f"{name}.kno"
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
        archive_zip.writestr("run.py", "print('remote-list-size')\n")
        archive_zip.writestr("requirements.txt", "")

    metadata_path = archive_path.parent / "manifest-metadata.json"
    metadata_path.write_text(
        (
            "{\n"
            f"  \"name\": \"{name}\",\n"
            f"  \"version\": \"{version}\",\n"
            f"  \"description\": \"{description}\"\n"
            "}\n"
        ),
        encoding="utf-8",
    )

    return archive_path


def test_pack_prints_human_readable_archive_size(tmp_path: Path) -> None:
    agent_dir = tmp_path / "size-line-agent"
    _create_agent_for_pack(agent_dir, name="size-line-agent", version="1.0.0", with_blob=False)

    archive_root = tmp_path / "archive-root"
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_script), "pack", str(agent_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert re.search(r"\[kinnoo pack\] Archive size: \d+(?:\.\d)? (?:B|KB|MB|GB)", output)


def test_pack_warns_when_archive_exceeds_threshold_override(tmp_path: Path) -> None:
    agent_dir = tmp_path / "size-warning-agent"
    _create_agent_for_pack(agent_dir, name="size-warning-agent", version="1.0.0", with_blob=True)

    archive_root = tmp_path / "archive-root"
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)
    env["KINNOO_PACK_WARN_THRESHOLD_MB"] = "1"

    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    result = subprocess.run(
        [sys.executable, str(cli_script), "pack", str(agent_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "[kinnoo pack] Archive size:" in output
    assert re.search(
        r"Warning: archive is large \([0-9]+\.[0-9] MB\)\. Consider whether all dependencies are necessary\.",
        output,
    )


def test_inspect_displays_archive_size_for_archive_target(tmp_path: Path) -> None:
    agent_dir = tmp_path / "inspect-size-agent"
    _create_agent_for_pack(agent_dir, name="inspect-size-agent", version="1.0.0", with_blob=False)

    archive_root = tmp_path / "archive-root"
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    pack_result = subprocess.run(
        [sys.executable, str(cli_script), "pack", str(agent_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    pack_output = f"{pack_result.stdout}\n{pack_result.stderr}"
    assert pack_result.returncode == 0, pack_output

    archives = sorted(archive_root.rglob("*.kno"))
    assert len(archives) == 1, "expected exactly one packed archive"

    inspect_result = subprocess.run(
        [sys.executable, str(cli_script), "inspect", str(archives[0])],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    inspect_output = f"{inspect_result.stdout}\n{inspect_result.stderr}"
    assert inspect_result.returncode == 0, inspect_output
    assert re.search(r"- Archive Size: \d+(?:\.\d)? (?:B|KB|MB|GB)", inspect_output)


def test_list_includes_archive_size(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-root"
    registry_root = tmp_path / "registry-root"

    _write_archive_summary_fixture(
        archive_root,
        name="list-local-agent",
        version="1.0.0",
        description="local list fixture",
    )
    _write_remote_summary_fixture(
        registry_root,
        name="list-remote-agent",
        version="2.0.0",
        description="remote list fixture",
    )

    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)
    env["KINNOO_REGISTRY_ROOT"] = str(registry_root)

    cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
    list_default = subprocess.run(
        [sys.executable, str(cli_script), "list"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    list_local = subprocess.run(
        [sys.executable, str(cli_script), "list", "--local"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )
    list_remote = subprocess.run(
        [sys.executable, str(cli_script), "list", "--remote"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
    )

    default_output = f"{list_default.stdout}\n{list_default.stderr}"
    local_output = f"{list_local.stdout}\n{list_local.stderr}"
    remote_output = f"{list_remote.stdout}\n{list_remote.stderr}"

    assert list_default.returncode == 0, default_output
    assert list_local.returncode == 0, local_output
    assert list_remote.returncode == 0, remote_output

    assert default_output == local_output
    assert "Local archive agents:" in default_output
    assert "list-local-agent | latest: 1.0.0 | description: local list fixture | size: " in default_output
    assert re.search(r"list-local-agent .*\| size: \d+(?:\.\d)? (?:B|KB|MB|GB)", default_output)

    assert "Remote registry agents:" in remote_output
    assert "list-remote-agent | latest: 2.0.0 | description: remote list fixture | size: " in remote_output
    assert re.search(r"list-remote-agent .*\| size: \d+(?:\.\d)? (?:B|KB|MB|GB)", remote_output)


def test_feature79_openclaw_pack_size_reporting_preserved(tmp_path: Path) -> None:
        agent_dir = tmp_path / "feature79-openclaw-size"
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "kinnoo.yaml").write_text(
                """
name: feature79-openclaw-size
version: 1.0.0
type: openclaw-skill
framework: openclaw
entrypoint: index.js
runtime:
    language: nodejs
    version: '>=20'
    type: daemon
dependencies: []
inputs:
    type: text
outputs:
    type: text
""".strip()
                + "\n",
                encoding="utf-8",
        )
        (agent_dir / "index.js").write_text("console.log('size')\n", encoding="utf-8")
        (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
        (agent_dir / "package.json").write_text('{"name":"feature79-openclaw-size"}\n', encoding="utf-8")
        (agent_dir / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        (agent_dir / "skills").mkdir(parents=True, exist_ok=True)
        (agent_dir / "skills" / "skill.md").write_text("skill\n", encoding="utf-8")

        archive_root = tmp_path / "archive-root"
        env = os.environ.copy()
        env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

        cli_script = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"
        result = subprocess.run(
                [sys.executable, str(cli_script), "pack", str(agent_dir)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                env=env,
        )

        output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode == 0, output
        assert re.search(r"\[kinnoo pack\] Archive size: \d+(?:\.\d)? (?:B|KB|MB|GB)", output)
