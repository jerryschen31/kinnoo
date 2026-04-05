from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI = ["python3", str(PROJECT_ROOT / "src" / "kinnoo" / "cli.py")]


def _env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archive-root")
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _archive(tmp_path: Path, name: str, version: str = "1.0.0") -> Path:
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
    (agent_dir / "run.py").write_text("print('install verify')\n", encoding="utf-8")
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")


def _pack_agent(tmp_path: Path, name: str, sign: bool) -> tuple[Path, Path | None]:
    agent_dir = tmp_path / name
    agent_dir.mkdir()
    _write_agent(agent_dir, name)

    args = ["pack", str(agent_dir)]
    private_key: Path | None = None
    if sign:
        key_dir = tmp_path / f"{name}-keys"
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
        args += ["--sign", "--signing-key", str(private_key)]

    pack_result = subprocess.run(
        CLI + args,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    assert pack_result.returncode == 0, pack_result.stdout + pack_result.stderr
    return _archive(tmp_path, name), private_key


def _tamper_archive(archive_path: Path, new_run_py: str) -> None:
    temp_archive = archive_path.with_suffix(".tmp.kno")
    with zipfile.ZipFile(archive_path, "r") as src, zipfile.ZipFile(temp_archive, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            if info.is_dir():
                continue
            payload = src.read(info.filename)
            if info.filename == "run.py":
                payload = new_run_py.encode("utf-8")
            dst.writestr(info.filename, payload)
    temp_archive.replace(archive_path)


def test_feature88_group1(tmp_path: Path) -> None:
    # Strict install path with signed archive should succeed.
    signed_archive, _ = _pack_agent(tmp_path, "feature88-signed", sign=True)
    strict_target = tmp_path / "strict-target"
    strict_result = subprocess.run(
        CLI + ["install", str(signed_archive), str(strict_target), "--yes", "--strict"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    strict_output = f"{strict_result.stdout}\n{strict_result.stderr}"
    assert strict_result.returncode == 0, strict_output
    assert "Embedded signature verified" in strict_output

    # Tampered archive should fail integrity verification and cleanup target.
    tampered_archive, _ = _pack_agent(tmp_path, "feature88-tampered", sign=False)
    _tamper_archive(tampered_archive, "print('tampered')\n")
    checksum_sidecar = Path(f"{tampered_archive}.sha256")
    if checksum_sidecar.exists():
        checksum_sidecar.unlink()

    tampered_target = tmp_path / "tampered-target"
    tampered_result = subprocess.run(
        CLI + ["install", str(tampered_archive), str(tampered_target), "--yes"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    tampered_output = f"{tampered_result.stdout}\n{tampered_result.stderr}"
    assert tampered_result.returncode != 0
    assert "Verification FAILED" in tampered_output
    assert not tampered_target.exists()

    # Strict mode must reject unsigned archive due missing signature metadata.
    unsigned_archive, _ = _pack_agent(tmp_path, "feature88-unsigned", sign=False)
    strict_unsigned_target = tmp_path / "strict-unsigned-target"
    strict_unsigned = subprocess.run(
        CLI + ["install", str(unsigned_archive), str(strict_unsigned_target), "--yes", "--strict"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    strict_unsigned_output = f"{strict_unsigned.stdout}\n{strict_unsigned.stderr}"
    assert strict_unsigned.returncode != 0
    assert "Strict mode requires valid signature metadata" in strict_unsigned_output

    # --skip-verify bypasses checks and allows installation of tampered payload.
    skip_target = tmp_path / "skip-target"
    skip_result = subprocess.run(
        CLI + ["install", str(tampered_archive), str(skip_target), "--yes", "--skip-verify"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    skip_output = f"{skip_result.stdout}\n{skip_result.stderr}"
    assert skip_result.returncode == 0, skip_output
    assert "Verification skipped" in skip_output


def test_feature88_group2(tmp_path: Path) -> None:
    # Backward compatibility: old archive without META-INF/integrity.json installs with warning.
    old_archive = tmp_path / "legacy-no-integrity.kno"
    with zipfile.ZipFile(old_archive, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "kinnoo.yaml",
            (
                "name: legacy-no-integrity\n"
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
        )
        archive.writestr("run.py", "print('legacy')\n")
        archive.writestr("requirements.txt", "")

    legacy_target = tmp_path / "legacy-target"
    legacy_result = subprocess.run(
        CLI + ["install", str(old_archive), str(legacy_target), "--yes"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    legacy_output = f"{legacy_result.stdout}\n{legacy_result.stderr}"
    assert legacy_result.returncode == 0, legacy_output
    assert "continuing for backward compatibility" in legacy_output

    # Valid archive logs verification summary line.
    valid_archive, _ = _pack_agent(tmp_path, "feature88-valid", sign=False)
    valid_target = tmp_path / "valid-target"
    valid_result = subprocess.run(
        CLI + [
            "install",
            str(valid_archive),
            str(valid_target),
            "--yes",
            "--allow-unverified-publisher",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=_env(tmp_path),
    )
    valid_output = f"{valid_result.stdout}\n{valid_result.stderr}"
    assert valid_result.returncode == 0, valid_output
    assert "Verified" in valid_output
    assert "all passed" in valid_output

    # Cleanup old archive install to keep tmp tree small for local runs.
    shutil.rmtree(legacy_target, ignore_errors=True)
