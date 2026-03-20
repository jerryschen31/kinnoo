import subprocess
import sys
import zipfile
import os
import json
import hashlib
from pathlib import Path

# Test51: kinnoo install usage error

def test_install_missing_archive_prints_usage():
    cli_path = "src/kinnoo/cli.py"
    result = subprocess.run([
        sys.executable, cli_path, "install"
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "Usage: kinnoo install <archive-path | agent_name[==version]> [target-dir]" in result.stderr


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
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), "--yes"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert expected_dir.exists()
    assert (expected_dir / "kinnoo.yaml").exists()


def _create_archive_with_missing_required_wheel(tmp_path: Path) -> Path:
    agent_dir = tmp_path / "fallback-agent-src"
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        """
name: fallback-agent
version: 1.0.0
entrypoint: run.py
runtime:
  type: one-shot
  language: python
  version: "3.10"
dependencies: []
inputs:
  type: string
outputs:
  type: string
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('fallback-ok')\n")
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\n")

    wheels_dir = agent_dir / "wheels"
    wheels_dir.mkdir()
    wheel_build = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "requests==2.31.0",
            "--wheel-dir",
            str(wheels_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert wheel_build.returncode == 0, wheel_build.stderr

    requests_wheels = sorted(wheels_dir.glob("requests-*.whl"))
    assert requests_wheels, "Expected requests wheel to exist before removal"
    requests_wheels[0].unlink()

    archive_path = tmp_path / "fallback-agent.kno"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.write(agent_dir / "kinnoo.yaml", arcname="kinnoo.yaml")
        archive.write(agent_dir / "run.py", arcname="run.py")
        archive.write(agent_dir / "requirements.txt", arcname="requirements.txt")
        for wheel in wheels_dir.glob("*.whl"):
            archive.write(wheel, arcname=f"wheels/{wheel.name}")

    return archive_path


def test_install_falls_back_to_pypi_when_wheel_missing(tmp_path):
    archive_path = _create_archive_with_missing_required_wheel(tmp_path)
    target_dir = tmp_path / "installed-fallback-agent"

    result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "Expected install to succeed via PyPI fallback when a required wheel is missing. "
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "Missing packaged wheels for dependencies: requests" in result.stderr
    assert "Falling back to PyPI; internet access is required." in result.stderr

    python_exe = target_dir / ".venv" / "bin" / "python"
    if not python_exe.exists():
        python_exe = target_dir / ".venv" / "Scripts" / "python.exe"

    import_check = subprocess.run(
        [str(python_exe), "-c", "import requests; print(requests.__version__)"],
        capture_output=True,
        text=True,
    )
    assert import_check.returncode == 0, import_check.stderr
    assert "2.31.0" in import_check.stdout


def _create_packed_archive_with_complete_transitive_wheels(tmp_path: Path, agent_name: str = "offline-ready-agent") -> Path:
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()

    (agent_dir / "kinnoo.yaml").write_text(
        f"""
name: {agent_name}
version: 1.0.0
entrypoint: run.py
runtime:
  type: one-shot
  language: python
  version: "3.10"
dependencies: []
inputs:
  type: string
outputs:
  type: string
""".strip()
        + "\n"
    )
    (agent_dir / "run.py").write_text("print('offline-ready-ok')\n")
    (agent_dir / "requirements.txt").write_text("requests==2.31.0\nhttpx==0.27.0\n")

    archive_root = tmp_path / "archive-root"
    pack_env = dict(os.environ)
    pack_env["KINNOO_ARCHIVE_ROOT"] = str(archive_root)

    pack_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "pack", str(agent_dir)],
        capture_output=True,
        text=True,
        env=pack_env,
    )
    assert pack_result.returncode == 0, (
        "Expected pack to succeed for offline-ready fixture. "
        f"STDOUT:\n{pack_result.stdout}\nSTDERR:\n{pack_result.stderr}"
    )

    archive_path = archive_root / agent_name / "1.0.0" / f"{agent_name}.kno"
    assert archive_path.exists(), (
        "Expected packed archive at canonical archive path. "
        f"STDOUT:\n{pack_result.stdout}\nSTDERR:\n{pack_result.stderr}"
    )

    return archive_path


def test_install_offline_succeeds_with_complete_wheels(tmp_path):
    # [agent] test69 validates AC5: complete bundled wheel sets should install
    # without network fallback when offline mode is explicitly enabled.
    archive_path = _create_packed_archive_with_complete_transitive_wheels(tmp_path)
    target_dir = tmp_path / "installed-offline-ready-agent"

    offline_env = dict(os.environ)
    offline_env["PIP_NO_INDEX"] = "1"
    offline_env["KINNOO_OFFLINE"] = "1"

    install_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(archive_path), str(target_dir), "--yes"],
        capture_output=True,
        text=True,
        env=offline_env,
    )
    assert install_result.returncode == 0, (
        "Expected offline install to succeed with complete wheels. "
        f"STDOUT:\n{install_result.stdout}\nSTDERR:\n{install_result.stderr}"
    )
    assert "Falling back to PyPI" not in install_result.stderr

    python_exe = target_dir / ".venv" / "bin" / "python"
    if not python_exe.exists():
        python_exe = target_dir / ".venv" / "Scripts" / "python.exe"

    dependency_check = subprocess.run(
        [str(python_exe), "-c", "import requests, httpx; print('ok')"],
        capture_output=True,
        text=True,
    )
    assert dependency_check.returncode == 0, dependency_check.stderr
    assert dependency_check.stdout.strip() == "ok"


def _create_node_archive(
    tmp_path: Path,
    agent_name: str = "feature37-node-agent",
    with_lifecycle_scripts: bool = False,
) -> Path:
    archive_path = tmp_path / f"{agent_name}.kno"
    manifest = (
        f"name: {agent_name}\n"
        "version: 1.0.0\n"
        "entrypoint: index.mjs\n"
        "runtime:\n"
        "  type: daemon\n"
        "  language: nodejs\n"
        "  version: \">=20.0.0\"\n"
        "  package_manager: npm\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )
    scripts_block = ""
    if with_lifecycle_scripts:
        scripts_block = (
            "  \"scripts\": {\n"
            "    \"prepare\": \"node ./scripts/prepare.mjs\",\n"
            "    \"postinstall\": \"node ./scripts/postinstall.mjs\"\n"
            "  },\n"
        )

    package_json = (
        "{\n"
        f"  \"name\": \"{agent_name}\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"type\": \"module\",\n"
        f"{scripts_block}"
        "  \"dependencies\": {\n"
        "    \"left-pad\": \"^1.3.0\"\n"
        "  }\n"
        "}\n"
    )
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("index.mjs", "console.log('hello node')\n")
        archive.writestr("package.json", package_json)
    return archive_path


def _create_feature39_permissions_archive(tmp_path: Path, agent_name: str = "feature39-consent-agent") -> Path:
    archive_path = tmp_path / f"{agent_name}.kno"
    manifest = (
        f"name: {agent_name}\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \"3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
        "permissions:\n"
        "  network: true\n"
        "  filesystem_scope: workspace-write\n"
        "  shell: false\n"
        "  browser: false\n"
        "  env_access:\n"
        "    - OPENAI_API_KEY\n"
        "    - KINNOO_ENV\n"
    )

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("run.py", "print('feature39-install-ok')\n")

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")

    return archive_path


def _create_feature40_unsigned_archive_with_checksum(
    tmp_path: Path,
    agent_name: str = "feature40-unsigned-publisher-agent",
) -> Path:
    archive_path = tmp_path / f"{agent_name}.kno"
    manifest = (
        f"name: {agent_name}\n"
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
        archive.writestr("run.py", "print('feature40-unsigned-ok')\n")

    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {archive_path.name}\n", encoding="utf-8")
    return archive_path


def _make_fake_node_toolchain(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)

    node_script = bin_dir / "node"
    node_script.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo v20.11.1\n"
        "  exit 0\n"
        "fi\n"
        "echo unsupported node invocation >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    node_script.chmod(0o755)

    npm_script = bin_dir / "npm"
    npm_script.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"install\" ]; then\n"
        "  if [ -n \"$KINNOO_TEST_NPM_ARGS_LOG\" ]; then\n"
        "    printf '%s\\n' \"$*\" > \"$KINNOO_TEST_NPM_ARGS_LOG\"\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"audit\" ] && [ \"$2\" = \"--json\" ]; then\n"
        "  cat <<'JSON'\n"
        "{\"metadata\":{\"vulnerabilities\":{\"critical\":1,\"high\":2,\"moderate\":3,\"low\":4}}}\n"
        "JSON\n"
        "  exit 1\n"
        "fi\n"
        "echo unsupported npm invocation >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    npm_script.chmod(0o755)


def test_feature37_node_audit_severity_summary(tmp_path):
    node_archive = _create_node_archive(tmp_path)
    node_target_dir = tmp_path / "feature37-node-installed"

    fake_bin = tmp_path / "fake-bin"
    _make_fake_node_toolchain(fake_bin)

    node_env = dict(os.environ)
    node_env["PATH"] = f"{fake_bin}{os.pathsep}{node_env.get('PATH', '')}"

    node_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(node_archive),
            str(node_target_dir),
            "--yes",
            "--allow-vulnerable",
        ],
        capture_output=True,
        text=True,
        env=node_env,
    )

    node_output = f"{node_result.stdout}\n{node_result.stderr}"
    assert node_result.returncode == 0, node_output
    assert "Node audit severity summary: critical=1 high=2 moderate=3 low=4" in node_output

    python_archive, _ = _create_valid_archive(tmp_path)
    python_target_dir = tmp_path / "feature37-python-installed"
    python_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(python_archive), str(python_target_dir), "--yes"],
        capture_output=True,
        text=True,
    )

    python_output = f"{python_result.stdout}\n{python_result.stderr}"
    assert python_result.returncode == 0, python_output
    assert "Node audit severity summary:" not in python_output


def test_feature37_critical_gate_default_block_and_allow_override(tmp_path):
    node_archive = _create_node_archive(tmp_path, agent_name="feature37-node-critical-gate")

    fake_bin = tmp_path / "fake-bin-critical"
    _make_fake_node_toolchain(fake_bin)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"

    blocked_target_dir = tmp_path / "feature37-node-critical-blocked"
    blocked_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(node_archive), str(blocked_target_dir), "--yes"],
        capture_output=True,
        text=True,
        env=env,
    )
    blocked_output = f"{blocked_result.stdout}\n{blocked_result.stderr}"
    assert blocked_result.returncode != 0, blocked_output
    assert "Node audit severity summary: critical=1 high=2 moderate=3 low=4" in blocked_output
    assert "--allow-vulnerable" in blocked_output
    assert "Critical vulnerabilities were detected" in blocked_output

    allowed_target_dir = tmp_path / "feature37-node-critical-allowed"
    allowed_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(node_archive),
            str(allowed_target_dir),
            "--yes",
            "--allow-vulnerable",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    allowed_output = f"{allowed_result.stdout}\n{allowed_result.stderr}"
    assert allowed_result.returncode == 0, allowed_output
    assert "Node audit severity summary: critical=1 high=2 moderate=3 low=4" in allowed_output
    assert "Continuing install despite critical vulnerabilities" in allowed_output


def test_feature37_lifecycle_scripts_warning_and_ignore_scripts_mode(tmp_path):
    node_archive = _create_node_archive(
        tmp_path,
        agent_name="feature37-node-lifecycle",
        with_lifecycle_scripts=True,
    )

    fake_bin = tmp_path / "fake-bin-lifecycle"
    _make_fake_node_toolchain(fake_bin)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"

    allowed_target_dir = tmp_path / "feature37-node-lifecycle-allowed"
    allowed_args_log = tmp_path / "npm-allowed-args.log"
    env["KINNOO_TEST_NPM_ARGS_LOG"] = str(allowed_args_log)
    allowed_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(node_archive),
            str(allowed_target_dir),
            "--yes",
            "--allow-vulnerable",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    allowed_output = f"{allowed_result.stdout}\n{allowed_result.stderr}"
    assert allowed_result.returncode == 0, allowed_output
    assert "Detected Node lifecycle scripts in package.json: postinstall, prepare." in allowed_output
    assert "Lifecycle scripts are allowed and may execute during dependency installation." in allowed_output
    assert allowed_args_log.read_text(encoding="utf-8").strip() == "install"

    ignored_target_dir = tmp_path / "feature37-node-lifecycle-ignored"
    ignored_args_log = tmp_path / "npm-ignored-args.log"
    env["KINNOO_TEST_NPM_ARGS_LOG"] = str(ignored_args_log)
    ignored_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(node_archive),
            str(ignored_target_dir),
            "--yes",
            "--allow-vulnerable",
            "--ignore-scripts",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    ignored_output = f"{ignored_result.stdout}\n{ignored_result.stderr}"
    assert ignored_result.returncode == 0, ignored_output
    assert "Detected Node lifecycle scripts in package.json: postinstall, prepare." in ignored_output
    assert "Lifecycle scripts policy: ignored (--ignore-scripts enabled)." in ignored_output
    assert ignored_args_log.read_text(encoding="utf-8").strip() == "install --ignore-scripts"


def test_feature37_install_trace_captures_audit_and_decisions(tmp_path):
    node_archive = _create_node_archive(
        tmp_path,
        agent_name="feature37-node-trace",
        with_lifecycle_scripts=True,
    )

    fake_bin = tmp_path / "fake-bin-trace"
    _make_fake_node_toolchain(fake_bin)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"

    blocked_target_dir = tmp_path / "feature37-node-trace-blocked"
    blocked_result = subprocess.run(
        [sys.executable, "src/kinnoo/cli.py", "install", str(node_archive), str(blocked_target_dir), "--yes"],
        capture_output=True,
        text=True,
        env=env,
    )
    blocked_output = f"{blocked_result.stdout}\n{blocked_result.stderr}"
    assert blocked_result.returncode != 0, blocked_output

    blocked_trace_path = blocked_target_dir / ".kinnoo" / "install-trace.json"
    assert blocked_trace_path.exists(), blocked_output
    blocked_trace = json.loads(blocked_trace_path.read_text(encoding="utf-8"))
    assert blocked_trace["schema_version"] == "1.0"
    assert blocked_trace["runtime_language"] == "nodejs"
    assert blocked_trace["package_manager"] == "npm"
    assert blocked_trace["lifecycle_scripts"] == {
        "detected": True,
        "names": ["postinstall", "prepare"],
        "policy": "allowed",
    }
    assert blocked_trace["audit"]["severity_counts"] == {
        "critical": 1,
        "high": 2,
        "moderate": 3,
        "low": 4,
    }
    assert blocked_trace["decision"] == {
        "outcome": "blocked",
        "reason": "critical_vulnerabilities_blocked",
        "allow_vulnerable": False,
        "ignore_scripts": False,
    }

    allowed_target_dir = tmp_path / "feature37-node-trace-allowed"
    allowed_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(node_archive),
            str(allowed_target_dir),
            "--yes",
            "--allow-vulnerable",
            "--ignore-scripts",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    allowed_output = f"{allowed_result.stdout}\n{allowed_result.stderr}"
    assert allowed_result.returncode == 0, allowed_output

    allowed_trace_path = allowed_target_dir / ".kinnoo" / "install-trace.json"
    assert allowed_trace_path.exists(), allowed_output
    allowed_trace = json.loads(allowed_trace_path.read_text(encoding="utf-8"))
    assert allowed_trace["schema_version"] == "1.0"
    assert allowed_trace["runtime_language"] == "nodejs"
    assert allowed_trace["package_manager"] == "npm"
    assert allowed_trace["lifecycle_scripts"] == {
        "detected": True,
        "names": ["postinstall", "prepare"],
        "policy": "ignored",
    }
    assert allowed_trace["audit"]["severity_counts"] == {
        "critical": 1,
        "high": 2,
        "moderate": 3,
        "low": 4,
    }
    assert allowed_trace["decision"] == {
        "outcome": "allowed",
        "reason": "critical_vulnerabilities_overridden",
        "allow_vulnerable": True,
        "ignore_scripts": True,
    }


def test_feature39_install_permission_summary_and_consent(tmp_path):
    permissions_archive = _create_feature39_permissions_archive(tmp_path)

    denied_target_dir = tmp_path / "feature39-consent-denied"
    denied_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(permissions_archive),
            str(denied_target_dir),
        ],
        input="n\n",
        capture_output=True,
        text=True,
    )
    denied_output = f"{denied_result.stdout}\n{denied_result.stderr}"
    assert denied_result.returncode != 0, denied_output
    assert "[kinnoo install] Install summary:" in denied_output
    assert "- Permissions:" in denied_output
    assert "Network: allowed" in denied_output
    assert "Filesystem Scope: workspace-write" in denied_output
    assert "Shell: denied" in denied_output
    assert "Browser: denied" in denied_output
    assert "Env Access: OPENAI_API_KEY, KINNOO_ENV" in denied_output
    assert "Install aborted: permissions consent not granted." in denied_output

    accepted_target_dir = tmp_path / "feature39-consent-accepted"
    accepted_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(permissions_archive),
            str(accepted_target_dir),
        ],
        input="y\ny\n",
        capture_output=True,
        text=True,
    )
    accepted_output = f"{accepted_result.stdout}\n{accepted_result.stderr}"
    assert accepted_result.returncode == 0, accepted_output
    assert "Allow requested permissions? [y/N]:" in accepted_output
    assert "Continue with install? [y/N]:" in accepted_output
    assert accepted_target_dir.exists(), accepted_output

    override_without_flag_target_dir = tmp_path / "feature39-consent-missing-override"
    override_without_flag_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(permissions_archive),
            str(override_without_flag_target_dir),
            "--yes",
        ],
        capture_output=True,
        text=True,
    )
    override_without_flag_output = (
        f"{override_without_flag_result.stdout}\n{override_without_flag_result.stderr}"
    )
    assert override_without_flag_result.returncode != 0, override_without_flag_output
    assert "--accept-permissions" in override_without_flag_output

    override_target_dir = tmp_path / "feature39-consent-override"
    override_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(permissions_archive),
            str(override_target_dir),
            "--yes",
            "--accept-permissions",
        ],
        capture_output=True,
        text=True,
    )
    override_output = f"{override_result.stdout}\n{override_result.stderr}"
    assert override_result.returncode == 0, override_output
    assert "Permissions consent acknowledged via --accept-permissions override." in override_output
    assert "- Permissions:" in override_output
    assert override_target_dir.exists(), override_output


def test_feature40_unsigned_archive_warning_and_confirmation(tmp_path):
    unsigned_archive = _create_feature40_unsigned_archive_with_checksum(tmp_path)

    denied_target_dir = tmp_path / "feature40-unsigned-denied"
    denied_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(unsigned_archive),
            str(denied_target_dir),
        ],
        input="n\n",
        capture_output=True,
        text=True,
    )
    denied_output = f"{denied_result.stdout}\n{denied_result.stderr}"
    assert denied_result.returncode != 0, denied_output
    assert "UNVERIFIED PUBLISHER" in denied_output
    assert "Install aborted: unverified publisher not approved." in denied_output

    override_target_dir = tmp_path / "feature40-unsigned-override"
    override_result = subprocess.run(
        [
            sys.executable,
            "src/kinnoo/cli.py",
            "install",
            str(unsigned_archive),
            str(override_target_dir),
            "--yes",
            "--allow-unverified-publisher",
        ],
        capture_output=True,
        text=True,
    )
    override_output = f"{override_result.stdout}\n{override_result.stderr}"
    assert override_result.returncode == 0, override_output
    assert "UNVERIFIED PUBLISHER" in override_output
    assert "Unverified publisher override acknowledged" in override_output
    assert override_target_dir.exists(), override_output
