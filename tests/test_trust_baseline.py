import subprocess
import sys
import zipfile
from pathlib import Path


def _create_trust_baseline_archive(tmp_path: Path, archive_name: str) -> Path:
    archive_path = tmp_path / f"{archive_name}.kno"
    manifest = (
        f"name: {archive_name}\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "dependencies: []\n"
        "env_vars:\n"
        "  - OPENAI_API_KEY\n"
        "  - ANTHROPIC_API_KEY\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("requirements.txt", "pip\n")
        archive.writestr("run.py", "print('ok')\n")

    return archive_path


def test_install_summary_and_confirmation_prompt(tmp_path: Path) -> None:
    archive_path = _create_trust_baseline_archive(tmp_path, "trust-agent")

    target_yes = tmp_path / "installed-trust-agent-yes"
    yes_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_yes)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    yes_output = f"{yes_result.stdout}\n{yes_result.stderr}"
    assert yes_result.returncode == 0, yes_output
    assert "[kinnoo install] Install summary:" in yes_output
    assert "- Agent: trust-agent" in yes_output
    assert "- Runtime Type: one-shot" in yes_output
    assert "- Dependencies:" in yes_output
    assert "  - pip" in yes_output
    assert "- Env Vars:" in yes_output
    assert "  - OPENAI_API_KEY" in yes_output
    assert "  - ANTHROPIC_API_KEY" in yes_output
    assert "Continue with install? [y/N]:" in yes_output
    assert target_yes.exists()

    target_no = tmp_path / "installed-trust-agent-no"
    no_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_no)],
        input="n\n",
        capture_output=True,
        text=True,
    )

    no_output = f"{no_result.stdout}\n{no_result.stderr}"
    assert no_result.returncode != 0
    assert "Continue with install? [y/N]:" in no_output
    assert "Install aborted by user." in no_output
    assert not target_no.exists()

    target_empty = tmp_path / "installed-trust-agent-empty"
    empty_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_empty)],
        input="\n",
        capture_output=True,
        text=True,
    )

    empty_output = f"{empty_result.stdout}\n{empty_result.stderr}"
    assert empty_result.returncode != 0
    assert "Continue with install? [y/N]:" in empty_output
    assert "Install aborted by user." in empty_output
    assert not target_empty.exists()


def test_install_yes_flag_bypasses_prompt(tmp_path: Path) -> None:
    archive_path = _create_trust_baseline_archive(tmp_path, "trust-agent-yes-flag")

    target_long_flag = tmp_path / "installed-yes-long"
    long_flag_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_long_flag),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )

    long_flag_output = f"{long_flag_result.stdout}\n{long_flag_result.stderr}"
    assert long_flag_result.returncode == 0, long_flag_output
    assert "[kinnoo install] Install summary:" in long_flag_output
    assert "- Runtime Type: one-shot" in long_flag_output
    assert "  - pip" in long_flag_output
    assert "  - OPENAI_API_KEY" in long_flag_output
    assert "Continue with install? [y/N]:" not in long_flag_output
    assert target_long_flag.exists()

    target_short_flag = tmp_path / "installed-yes-short"
    short_flag_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_short_flag),
            "-y",
        ],
        capture_output=True,
        text=True,
    )

    short_flag_output = f"{short_flag_result.stdout}\n{short_flag_result.stderr}"
    assert short_flag_result.returncode == 0, short_flag_output
    assert "[kinnoo install] Install summary:" in short_flag_output
    assert "- Runtime Type: one-shot" in short_flag_output
    assert "  - pip" in short_flag_output
    assert "  - OPENAI_API_KEY" in short_flag_output
    assert "Continue with install? [y/N]:" not in short_flag_output
    assert target_short_flag.exists()
