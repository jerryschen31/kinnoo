import subprocess
import sys
import zipfile
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
