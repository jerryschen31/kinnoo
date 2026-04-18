from __future__ import annotations

import base64
import json
import os
import subprocess
import zipfile
from pathlib import Path

from src.kinnoo.signing import load_ed25519_public_key, verify_signature


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI = ["python3", str(PROJECT_ROOT / "src" / "kinnoo" / "cli.py")]


def _env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _archive(tmp_path: Path, name: str, version: str) -> Path:
    return tmp_path / "archive-root" / name / version / f"{name}.kno"


def _write_agent(agent_dir: Path, name: str) -> None:
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
    (agent_dir / "run.py").write_text("print('signed')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")


def test_feature87_group1(tmp_path: Path) -> None:
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    private_key = key_dir / "private.pem"
    public_key = key_dir / "public.pem"

    keygen_result = subprocess.run(
        CLI + ["keygen", "--private-key", str(private_key), "--public-key", str(public_key)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    assert keygen_result.returncode == 0, keygen_result.stdout + keygen_result.stderr

    agent_name = "feature87-signed"
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    _write_agent(agent_dir, agent_name)

    pack_result = subprocess.run(
        CLI + ["pack", str(agent_dir), "--sign", "--signing-key", str(private_key)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    assert pack_result.returncode == 0, pack_result.stdout + pack_result.stderr

    archive_path = _archive(tmp_path, agent_name, "1.0.0")
    with zipfile.ZipFile(archive_path, "r") as archive_file:
        names = set(archive_file.namelist())
        assert "META-INF/integrity.json" in names
        assert "META-INF/signature.json" in names

        integrity_bytes = archive_file.read("META-INF/integrity.json")
        signature_doc = json.loads(archive_file.read("META-INF/signature.json").decode("utf-8"))

    assert isinstance(signature_doc.get("signature"), str)
    assert isinstance(signature_doc.get("public_key_fingerprint"), str)
    assert isinstance(signature_doc.get("signed_at"), str)

    signature_bytes = base64.b64decode(signature_doc["signature"].encode("ascii"))
    signing_public_key = load_ed25519_public_key(public_key)
    assert verify_signature(signing_public_key, integrity_bytes, signature_bytes) is True


def test_feature87_group2(tmp_path: Path) -> None:
    agent_name = "feature87-unsigned"
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    _write_agent(agent_dir, agent_name)

    pack_result = subprocess.run(
        CLI + ["pack", str(agent_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    assert pack_result.returncode == 0, pack_result.stdout + pack_result.stderr

    archive_path = _archive(tmp_path, agent_name, "1.0.0")
    with zipfile.ZipFile(archive_path, "r") as archive_file:
        names = set(archive_file.namelist())
    assert "META-INF/integrity.json" in names
    assert "META-INF/signature.json" not in names
