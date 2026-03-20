import os
import shutil
import subprocess
import tempfile
import json
import base64
from pathlib import Path
import pytest

def make_dummy_kno_archive(archive_path, files=None):
    import zipfile
    files = files or {
        "kinnoo.yaml": (
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
        ),
        "run.py": "print('hello')\n"
    }
    with zipfile.ZipFile(archive_path, "w") as z:
        for fname, content in files.items():
            z.writestr(fname, content)

@pytest.mark.integration
def test_install_extracts_to_user_specified_directory(tmp_path):
    # Setup: create dummy .kno archive
    archive_path = tmp_path / "test-agent.kno"
    make_dummy_kno_archive(archive_path)
    target_dir = tmp_path / "myagent_dir"

    # Step1: Run kinnoo install <archive.kno> myagent_dir
    result = subprocess.run([
        "python3", "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"Install failed: {result.stderr}"
    assert target_dir.exists(), "Target directory not created"
    assert (target_dir / "kinnoo.yaml").exists(), "kinnoo.yaml missing"
    assert (target_dir / "run.py").exists(), "run.py missing"

    # Step2: Run kinnoo install <archive.kno> myagent_dir when directory exists (without --force)
    result2 = subprocess.run([
        "python3", "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"
    ], capture_output=True, text=True)
    assert result2.returncode != 0, "Should fail if directory exists and --force not used"
    assert "already exists" in result2.stderr, "Error message missing for existing directory"

    # Step3: --force is paused; skip this step


def _node_manifest_yaml(package_manager: str | None = None) -> str:
    package_manager_line = ""
    if package_manager is not None:
        package_manager_line = f"  package_manager: {package_manager}\n"

    return (
        "name: feature31-node-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.js\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: nodejs\n"
        f"{package_manager_line}"
        "  version: \">=22\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )


@pytest.mark.integration
def test_feature31_node_dependency_install_npm_and_pnpm(monkeypatch, tmp_path, capsys):
    from kinnoo import install_command

    monkeypatch.setattr(
        install_command,
        "check_node_runtime_constraint",
        lambda _constraint: (True, "runtime version check passed: current Node 22.0.0 satisfies runtime.version '>=22'"),
    )

    def _fake_package_manager_check(package_manager: str):
        if package_manager == "pnpm":
            return True, "dependency readiness check passed: node package manager 'pnpm' is available at /mock/pnpm"
        return True, "dependency readiness check passed: node package manager 'npm' is available at /mock/npm"

    monkeypatch.setattr(
        install_command,
        "check_node_package_manager_availability",
        _fake_package_manager_check,
    )

    calls: list[tuple[list[str], Path | None]] = []
    state = {"fail_pnpm": False}

    class _Completed:
        def __init__(self, returncode: int, stderr_text: str = ""):
            self.returncode = returncode
            self.stderr = stderr_text
            self.stdout = ""

    def _fake_run(command, *args, **kwargs):
        del args
        cwd = kwargs.get("cwd")
        calls.append((list(command), cwd))
        executable = Path(command[0]).name
        if executable == "npm":
            return _Completed(0)
        if executable == "pnpm":
            if state["fail_pnpm"]:
                return _Completed(12, "pnpm simulated failure")
            return _Completed(0)
        return _Completed(0)

    monkeypatch.setattr(install_command.subprocess, "run", _fake_run)

    # Scenario 1: runtime.package_manager omitted -> defaults to npm.
    npm_archive = tmp_path / "feature31-node-npm.kno"
    make_dummy_kno_archive(
        npm_archive,
        files={
            "kinnoo.yaml": _node_manifest_yaml(),
            "run.js": "console.log('ok')\n",
            "package.json": '{"name":"feature31-node-agent","version":"1.0.0"}\n',
        },
    )
    npm_target = tmp_path / "installed-npm"
    npm_result = install_command.install_agent(
        archive_path=str(npm_archive),
        target_dir_arg=str(npm_target),
        assume_yes=True,
    )
    assert npm_result == 0
    assert (["npm", "install"], npm_target) in calls

    # Scenario 2: runtime.package_manager set to pnpm -> use pnpm install.
    pnpm_archive = tmp_path / "feature31-node-pnpm.kno"
    make_dummy_kno_archive(
        pnpm_archive,
        files={
            "kinnoo.yaml": _node_manifest_yaml("pnpm"),
            "run.js": "console.log('ok')\n",
            "package.json": '{"name":"feature31-node-agent","version":"1.0.0"}\n',
        },
    )
    pnpm_target = tmp_path / "installed-pnpm"
    pnpm_result = install_command.install_agent(
        archive_path=str(pnpm_archive),
        target_dir_arg=str(pnpm_target),
        assume_yes=True,
    )
    assert pnpm_result == 0
    assert (["pnpm", "install"], pnpm_target) in calls

    # Scenario 3: package-manager install failure returns actionable error output.
    state["fail_pnpm"] = True
    pnpm_fail_archive = tmp_path / "feature31-node-pnpm-fail.kno"
    make_dummy_kno_archive(
        pnpm_fail_archive,
        files={
            "kinnoo.yaml": _node_manifest_yaml("pnpm"),
            "run.js": "console.log('ok')\n",
            "package.json": '{"name":"feature31-node-agent","version":"1.0.0"}\n',
        },
    )
    pnpm_fail_target = tmp_path / "installed-pnpm-fail"
    pnpm_fail_result = install_command.install_agent(
        archive_path=str(pnpm_fail_archive),
        target_dir_arg=str(pnpm_fail_target),
        assume_yes=True,
    )
    assert pnpm_fail_result != 0
    captured = capsys.readouterr()
    assert "Node dependency installation failed while running 'pnpm install'" in captured.err
    assert "pnpm simulated failure" in captured.err


def test_feature35_install_state_overwrite_warning_and_force(tmp_path):
    """Feature35 test294: install warns/preserves existing state by default and overwrites with explicit control."""
    archive_path = tmp_path / "feature35-state-restore.kno"
    make_dummy_kno_archive(
        archive_path,
        files={
            "kinnoo.yaml": (
                "name: feature35-agent\n"
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
                "state_dirs:\n"
                "  - memory\n"
            ),
            "run.py": "print('hello')\n",
            "requirements.txt": "",
            "memory/existing.txt": "keep-me\n",
            "state_snapshots/memory/from_snapshot.txt": "snapshot-state\n",
        },
    )

    target_no_overwrite = tmp_path / "installed-no-overwrite"
    result_no_overwrite = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_no_overwrite),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )
    assert result_no_overwrite.returncode == 0, result_no_overwrite.stderr
    assert "Existing state directory detected" in result_no_overwrite.stderr
    assert (target_no_overwrite / "memory" / "existing.txt").exists()
    assert not (target_no_overwrite / "memory" / "from_snapshot.txt").exists()

    target_with_overwrite = tmp_path / "installed-with-overwrite"
    result_with_overwrite = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_with_overwrite),
            "--yes",
            "--state-overwrite",
        ],
        capture_output=True,
        text=True,
    )
    assert result_with_overwrite.returncode == 0, result_with_overwrite.stderr
    assert (target_with_overwrite / "memory" / "from_snapshot.txt").exists()
    assert not (target_with_overwrite / "memory" / "existing.txt").exists()


def test_feature40_install_signature_verification_gate(tmp_path):
    from src.kinnoo.signing import create_detached_signature_artifacts, generate_ed25519_keypair

    private_key_path = tmp_path / "publisher-private.pem"
    public_key_path = tmp_path / "publisher-public.pem"
    generate_ed25519_keypair(private_key_path=private_key_path, public_key_path=public_key_path)

    valid_archive = tmp_path / "feature40-signed-valid.kno"
    make_dummy_kno_archive(valid_archive)
    create_detached_signature_artifacts(
        archive_path=valid_archive,
        private_key_path=private_key_path,
    )

    valid_target = tmp_path / "installed-feature40-valid"
    valid_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(valid_archive),
            str(valid_target),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )
    valid_output = f"{valid_result.stdout}\n{valid_result.stderr}"
    assert valid_result.returncode == 0, valid_output
    assert "Archive signature verified" in valid_output
    assert (valid_target / "kinnoo.yaml").exists()

    invalid_archive = tmp_path / "feature40-signed-invalid.kno"
    make_dummy_kno_archive(invalid_archive)
    create_detached_signature_artifacts(
        archive_path=invalid_archive,
        private_key_path=private_key_path,
    )

    invalid_signature_metadata_path = Path(f"{invalid_archive}.sig.json")
    invalid_metadata = json.loads(invalid_signature_metadata_path.read_text(encoding="utf-8"))
    invalid_metadata["signature_base64"] = base64.b64encode(b"feature40-invalid-signature").decode("ascii")
    invalid_signature_metadata_path.write_text(
        json.dumps(invalid_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    invalid_target = tmp_path / "installed-feature40-invalid"
    invalid_result = subprocess.run(
        [
            "python3",
            "src/kinnoo/cli.py",
            "install",
            str(invalid_archive),
            str(invalid_target),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )
    invalid_output = f"{invalid_result.stdout}\n{invalid_result.stderr}"
    assert invalid_result.returncode != 0
    assert "Signature verification failed" in invalid_output
    assert "Archive authenticity could not be verified" in invalid_output
