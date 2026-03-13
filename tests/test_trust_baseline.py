import subprocess
import sys
import zipfile
import json
import re
import os
from pathlib import Path

from kinnoo.checksum import write_checksum_sidecar_for_archive


def _create_trust_baseline_archive(
    tmp_path: Path,
    archive_name: str,
    create_checksum: bool = False,
) -> Path:
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

    if create_checksum:
        write_checksum_sidecar_for_archive(archive_path)

    return archive_path


def test_install_summary_and_confirmation_prompt(tmp_path: Path) -> None:
    archive_path = _create_trust_baseline_archive(
        tmp_path,
        "trust-agent",
        create_checksum=True,
    )

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
    archive_path = _create_trust_baseline_archive(
        tmp_path,
        "trust-agent-yes-flag",
        create_checksum=True,
    )

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


def test_install_unverified_source_warning(tmp_path: Path) -> None:
    archive_path = _create_trust_baseline_archive(tmp_path, "trust-agent-unverified")

    target_abort = tmp_path / "installed-unverified-abort"
    abort_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_abort)],
        input="n\n",
        capture_output=True,
        text=True,
    )

    abort_output = f"{abort_result.stdout}\n{abort_result.stderr}"
    assert abort_result.returncode != 0
    assert "This agent is from an unverified source." in abort_output
    assert "This agent is from an unverified source. Continue? (y/n):" in abort_output
    assert "Install aborted by user." in abort_output
    assert not target_abort.exists()

    target_yes = tmp_path / "installed-unverified-yes"
    yes_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_yes),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )

    yes_output = f"{yes_result.stdout}\n{yes_result.stderr}"
    assert yes_result.returncode == 0, yes_output
    assert "This agent is from an unverified source." in yes_output
    assert "This agent is from an unverified source. Continue? (y/n):" not in yes_output
    assert target_yes.exists()

    write_checksum_sidecar_for_archive(archive_path)

    target_verified = tmp_path / "installed-verified"
    verified_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(archive_path),
            str(target_verified),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )

    verified_output = f"{verified_result.stdout}\n{verified_result.stderr}"
    assert verified_result.returncode == 0, verified_output
    assert "This agent is from an unverified source." not in verified_output
    assert target_verified.exists()


def _create_run_trace_agent(tmp_path: Path, agent_name: str) -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        (
            f"name: {agent_name}\n"
            "version: 1.2.0\n"
            "entrypoint: run.py\n"
            "runtime:\n"
            "  type: one-shot\n"
            "  language: python\n"
            "  version: \">=3.10\"\n"
            "dependencies: []\n"
            "env_vars:\n"
            "  - TRACE_SECRET\n"
            "inputs:\n"
            "  type: string\n"
            "outputs:\n"
            "  type: string\n"
        ),
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text(
        "import sys\n"
        "print(f'run input: {sys.argv[1] if len(sys.argv) > 1 else ''}')\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")
    return agent_dir


def _latest_run_trace_log(home_dir: Path) -> Path:
    logs_dir = home_dir / ".kinnoo" / "logs"
    log_files = sorted(logs_dir.glob("run.*.log"))
    assert log_files, f"Expected run trace logs in {logs_dir}"
    return log_files[-1]


def test_run_trace_log_safe_fields(tmp_path: Path) -> None:
    agent_dir = _create_run_trace_agent(tmp_path, "trace-safe-agent")
    env = dict()
    env.update({"HOME": str(tmp_path), "TRACE_SECRET": "SAFE_TRACE_SECRET"})

    run_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            "hello-trace",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert run_result.returncode == 0, f"STDOUT:\n{run_result.stdout}\nSTDERR:\n{run_result.stderr}"

    log_path = _latest_run_trace_log(tmp_path)
    assert re.fullmatch(r"run\.\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z\.log", log_path.name)

    log_text = log_path.read_text(encoding="utf-8")
    payload = json.loads(log_text)

    assert set(payload.keys()) == {"timestamp", "agent_name", "agent-version", "runtime_type", "exit_code"}
    assert payload["agent_name"] == "trace-safe-agent"
    assert payload["agent-version"] == "1.2.0"
    assert payload["runtime_type"] == "one-shot"
    assert payload["exit_code"] == 0
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", payload["timestamp"])
    assert "hello-trace" not in log_text


def test_run_trace_log_no_secrets(tmp_path: Path) -> None:
    agent_dir = _create_run_trace_agent(tmp_path, "trace-no-secret-agent")
    secret_value = "SECRET_VALUE_12345"
    undeclared_secret_value = "UNDECLARED_SECRET_67890"
    input_text = "SENSITIVE_INPUT_98765"
    env = dict()
    env.update(
        {
            "HOME": str(tmp_path),
            "TRACE_SECRET": secret_value,
            "OPENAI_API_KEY": undeclared_secret_value,
        }
    )

    run_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "run",
            str(agent_dir),
            input_text,
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    assert run_result.returncode == 0, f"STDOUT:\n{run_result.stdout}\nSTDERR:\n{run_result.stderr}"

    log_path = _latest_run_trace_log(tmp_path)
    log_text = log_path.read_text(encoding="utf-8")
    payload = json.loads(log_text)

    assert set(payload.keys()) == {"timestamp", "agent_name", "agent-version", "runtime_type", "exit_code"}
    assert payload["agent_name"] == "trace-no-secret-agent"
    assert payload["agent-version"] == "1.2.0"
    assert payload["runtime_type"] == "one-shot"
    assert secret_value not in log_text
    assert undeclared_secret_value not in log_text
    assert input_text not in log_text


def _assert_anchor_has_invariant_comment(file_path: Path, anchor_text: str) -> None:
    source_lines = file_path.read_text(encoding="utf-8").splitlines()
    anchor_indices = [index for index, line in enumerate(source_lines) if anchor_text in line]
    assert anchor_indices, f"Anchor not found in {file_path}: {anchor_text}"

    for anchor_index in anchor_indices:
        window_start = max(0, anchor_index - 4)
        context_window = source_lines[window_start:anchor_index + 1]
        has_invariant_comment = any(
            "SECURITY INVARIANT: only env var NAMES, never values" in context_line
            for context_line in context_window
        )
        assert has_invariant_comment, (
            f"Missing security invariant comment near anchor '{anchor_text}' in {file_path}"
        )


def test_trust_code_has_security_invariant_comments() -> None:
    root_dir = Path(__file__).resolve().parents[1]

    install_file = root_dir / "src" / "kinnoo" / "install_command.py"
    run_file = root_dir / "src" / "kinnoo" / "run_command.py"
    inspect_file = root_dir / "src" / "kinnoo" / "inspect_command.py"

    _assert_anchor_has_invariant_comment(install_file, 'print("- Env Vars:")')
    _assert_anchor_has_invariant_comment(
        run_file,
        'return False, f"env vars check failed: unresolved env vars [{missing_label}]"',
    )
    _assert_anchor_has_invariant_comment(
        run_file,
        'return True, f"env vars check passed: resolved env vars [{declared_label}]"',
    )
    _assert_anchor_has_invariant_comment(run_file, "log_file.write_text(serialized_payload, encoding=\"utf-8\")")
    _assert_anchor_has_invariant_comment(inspect_file, 'print("- Env Vars:")')


def _create_security_sweep_agent(tmp_path: Path, agent_name: str, dirty: bool) -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        (
            f"name: {agent_name}\n"
            "version: 1.0.0\n"
            "entrypoint: run.py\n"
            "runtime:\n"
            "  type: one-shot\n"
            "  language: python\n"
            "  version: \"3.10\"\n"
            "dependencies: []\n"
            "env_vars:\n"
            "  - API_KEY\n"
            "inputs:\n"
            "  type: string\n"
            "outputs:\n"
            "  type: string\n"
        ),
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")

    if dirty:
        run_py = (
            "import os\n"
            "print(os.environ.get('API_KEY'))\n"
        )
    else:
        run_py = "print('safe')\n"

    (agent_dir / "run.py").write_text(run_py, encoding="utf-8")

    venv_dir = agent_dir / ".venv"
    venv_dir.mkdir()
    (venv_dir / "ignored.py").write_text(
        "import os\nprint(os.environ.get('SHOULD_NOT_APPEAR'))\n",
        encoding="utf-8",
    )

    return agent_dir


def test_inspect_security_sweep(tmp_path: Path) -> None:
    clean_agent = _create_security_sweep_agent(tmp_path, "inspect-clean-agent", dirty=False)
    clean_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect", str(clean_agent)],
        capture_output=True,
        text=True,
    )

    clean_output = f"{clean_result.stdout}\n{clean_result.stderr}"
    assert clean_result.returncode == 0, clean_output
    assert "Security sweep: no env var exposure patterns detected (heuristic)" in clean_output
    assert "(heuristic scan — may produce false positives; not a substitute for code review)" in clean_output
    assert "ignored.py" not in clean_output

    dirty_agent = _create_security_sweep_agent(tmp_path, "inspect-dirty-agent", dirty=True)
    dirty_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "inspect", str(dirty_agent)],
        capture_output=True,
        text=True,
    )

    dirty_output = f"{dirty_result.stdout}\n{dirty_result.stderr}"
    assert dirty_result.returncode == 0, dirty_output
    assert "Security sweep:" in dirty_output
    assert "run.py:" in dirty_output
    assert "print() with os.environ access" in dirty_output
    assert "(heuristic scan — may produce false positives; not a substitute for code review)" in dirty_output
    assert "ignored.py" not in dirty_output


def test_pack_security_sweep_non_blocking(tmp_path: Path) -> None:
    dirty_agent = _create_security_sweep_agent(tmp_path, "pack-dirty-agent", dirty=True)
    dirty_env = os.environ.copy()
    dirty_env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archives")
    dirty_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(dirty_agent)],
        capture_output=True,
        text=True,
        env=dirty_env,
    )

    dirty_output = f"{dirty_result.stdout}\n{dirty_result.stderr}"
    assert dirty_result.returncode == 0, dirty_output
    assert "Security sweep warnings:" in dirty_output
    assert "run.py:" in dirty_output
    assert "print() with os.environ access" in dirty_output
    assert "(heuristic scan — may produce false positives; not a substitute for code review)" in dirty_output
    assert "[kinnoo pack] Archive created:" in dirty_output

    clean_agent = _create_security_sweep_agent(tmp_path, "pack-clean-agent", dirty=False)
    clean_env = os.environ.copy()
    clean_env["KINNOO_ARCHIVE_ROOT"] = str(tmp_path / "archives")
    clean_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(clean_agent)],
        capture_output=True,
        text=True,
        env=clean_env,
    )

    clean_output = f"{clean_result.stdout}\n{clean_result.stderr}"
    assert clean_result.returncode == 0, clean_output
    assert "Security sweep warnings:" not in clean_output
    assert "[kinnoo pack] Archive created:" in clean_output
