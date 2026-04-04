from __future__ import annotations

import json
import os
import subprocess
import zipfile
from pathlib import Path

from src.kinnoo.integrity import compute_integrity_manifest, verify_integrity_manifest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI = ["python3", str(PROJECT_ROOT / "src" / "kinnoo" / "cli.py")]


def _pack_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _archive_path(tmp_path: Path, name: str, version: str) -> Path:
    return tmp_path / "archive-root" / name / version / f"{name}.kno"


def _write_minimal_agent(agent_dir: Path, name: str) -> None:
    (agent_dir / "kinnoo.yaml").write_text(
        (
            f"name: {name}\n"
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
        ),
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")


def test_feature86_group1(tmp_path: Path) -> None:
    agent_name = "feature86-agent"
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    _write_minimal_agent(agent_dir, agent_name)

    pack_result = subprocess.run(
        CLI + ["pack", str(agent_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_pack_env(tmp_path),
    )
    assert pack_result.returncode == 0, pack_result.stdout + pack_result.stderr

    archive = _archive_path(tmp_path, agent_name, "1.0.0")
    assert archive.exists()

    with zipfile.ZipFile(archive, "r") as archive_file:
        names = archive_file.namelist()
        assert "META-INF/integrity.json" in names

        manifest = json.loads(archive_file.read("META-INF/integrity.json").decode("utf-8"))
        assert manifest["version"] == 1
        assert isinstance(manifest["files"], dict)

        # Manifest should include regular files and never include META-INF entries.
        assert "kinnoo.yaml" in manifest["files"]
        assert "run.py" in manifest["files"]
        assert "requirements.txt" in manifest["files"]
        assert all(not path.startswith("META-INF/") for path in manifest["files"].keys())

    extracted = tmp_path / "extracted"
    extracted.mkdir()
    with zipfile.ZipFile(archive, "r") as archive_file:
        archive_file.extractall(extracted)

    recomputed = compute_integrity_manifest(extracted)
    assert recomputed == manifest

    mismatches = verify_integrity_manifest(extracted, manifest)
    assert mismatches == []
