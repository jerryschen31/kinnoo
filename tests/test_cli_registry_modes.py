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


def _write_minimal_python_agent(agent_dir: Path) -> None:
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "kinnoo.yaml").write_text(
        "\n".join(
            [
                "name: feature85-legacy-run-agent",
                "version: 1.0.0",
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
        encoding="utf-8",
    )
    (agent_dir / "run.py").write_text(
        "import sys\n"
        "print('legacy-run-ok', sys.argv[1] if len(sys.argv) > 1 else '')\n",
        encoding="utf-8",
    )
    (agent_dir / "requirements.txt").write_text("", encoding="utf-8")


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


def test_source_mode_argument_validation_errors(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-sandbox"
    registry_root = tmp_path / "registry-sandbox"

    env = {
        **os.environ,
        "KINNOO_ARCHIVE_ROOT": str(archive_root),
        "KINNOO_REGISTRY_ROOT": str(registry_root),
    }

    list_conflict = subprocess.run(
        [sys.executable, str(CLI_PATH), "list", "--local", "--remote"],
        capture_output=True,
        text=True,
        env=env,
    )
    search_conflict = subprocess.run(
        [sys.executable, str(CLI_PATH), "search", "--local", "--remote", "alpha"],
        capture_output=True,
        text=True,
        env=env,
    )
    search_missing_query = subprocess.run(
        [sys.executable, str(CLI_PATH), "search"],
        capture_output=True,
        text=True,
        env=env,
    )
    install_bad_selector = subprocess.run(
        [sys.executable, str(CLI_PATH), "install", "bad-agent==invalid"],
        capture_output=True,
        text=True,
        env=env,
    )

    list_conflict_output = f"{list_conflict.stdout}\n{list_conflict.stderr}"
    search_conflict_output = f"{search_conflict.stdout}\n{search_conflict.stderr}"
    search_missing_query_output = f"{search_missing_query.stdout}\n{search_missing_query.stderr}"
    install_bad_selector_output = f"{install_bad_selector.stdout}\n{install_bad_selector.stderr}"

    assert list_conflict.returncode != 0
    assert "not allowed with argument" in list_conflict_output

    assert search_conflict.returncode != 0
    assert "not allowed with argument" in search_conflict_output

    assert search_missing_query.returncode != 0
    assert "Usage: kinnoo search [--local | --remote] <query>" in search_missing_query_output

    assert install_bad_selector.returncode != 0
    assert "Invalid registry version 'invalid'. Expected semver." in install_bad_selector_output


def test_feature55_proxy_rewrite_forwarding() -> None:
    next_config = Path(__file__).resolve().parents[1] / "web" / "next.config.ts"
    text = next_config.read_text(encoding="utf-8")

    # AC1: /api/* rewrite target must be env-driven and default to localhost backend.
    assert "process.env.BACKEND_URL" in text
    assert "http://localhost:8000" in text
    assert 'source: "/api/:path*"' in text
    assert 'destination: `${backendUrl}/api/:path*`' in text

    # Forwarding semantics are contractually preserved by proxy rewrites with pass-through headers.
    assert "X-Forwarded-For" in text or "forwarded" in text.lower()
    assert "X-Request-Id" in text or "request-id" in text.lower()


def test_feature67_sync_modes_and_upsert(tmp_path: Path) -> None:
    """Feature67 deprecated-path coverage: legacy sync remains functional during migration."""
    registry_root = tmp_path / "registry-sandbox"
    fixture_path = tmp_path / "clawhub-sync-fixture.json"

    first_payload = {
        "items": [
            {
                "slug": "owner-alpha/agent-alpha",
                "version": "1.0.0",
                "source_url": "https://clawhub.dev/owner-alpha/agent-alpha",
                "metadata": {"title": "Agent Alpha"},
            },
            {
                "slug": "owner-beta/agent-beta",
                "version": "2.1.0",
                "source_url": "https://clawhub.dev/owner-beta/agent-beta",
                "metadata": {"title": "Agent Beta"},
            },
        ]
    }
    fixture_path.write_text(json.dumps(first_payload, indent=2) + "\n", encoding="utf-8")

    env = {
        **os.environ,
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "KINNOO_CLAWHUB_SYNC_FIXTURE": str(fixture_path),
    }

    incremental_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "sync", "clawhub"],
        capture_output=True,
        text=True,
        env=env,
    )
    incremental_output = f"{incremental_result.stdout}\n{incremental_result.stderr}"
    assert incremental_result.returncode == 0, incremental_output
    assert "source=clawhub mode=incremental created=2 updated=0 skipped=0 failed=0" in incremental_output

    alpha_record_path = (
        registry_root
        / "tenants"
        / "clawhub"
        / "mirror"
        / "owner-alpha"
        / "agent-alpha"
        / "1.0.0"
        / "mirror-record.json"
    )
    beta_record_path = (
        registry_root
        / "tenants"
        / "clawhub"
        / "mirror"
        / "owner-beta"
        / "agent-beta"
        / "2.1.0"
        / "mirror-record.json"
    )
    assert alpha_record_path.exists(), incremental_output
    assert beta_record_path.exists(), incremental_output

    alpha_record = json.loads(alpha_record_path.read_text(encoding="utf-8"))
    assert alpha_record["tenant_slug"] == "clawhub"
    assert alpha_record["source_registry"] == "clawhub"
    assert alpha_record["source_slug"] == "owner-alpha/agent-alpha"

    second_payload = {
        "items": [
            {
                "slug": "owner-alpha/agent-alpha",
                "version": "1.1.0",
                "source_url": "https://clawhub.dev/owner-alpha/agent-alpha",
                "metadata": {"title": "Agent Alpha"},
            },
            {
                "slug": "owner-beta/agent-beta",
                "version": "2.1.0",
                "source_url": "https://clawhub.dev/owner-beta/agent-beta",
                "metadata": {"title": "Agent Beta"},
            },
        ]
    }
    fixture_path.write_text(json.dumps(second_payload, indent=2) + "\n", encoding="utf-8")

    full_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "sync", "clawhub", "--full"],
        capture_output=True,
        text=True,
        env=env,
    )
    full_output = f"{full_result.stdout}\n{full_result.stderr}"
    assert full_result.returncode == 0, full_output
    assert "source=clawhub mode=full created=0 updated=1 skipped=1 failed=0" in full_output

    alpha_updated_path = (
        registry_root
        / "tenants"
        / "clawhub"
        / "mirror"
        / "owner-alpha"
        / "agent-alpha"
        / "1.1.0"
        / "mirror-record.json"
    )
    assert alpha_updated_path.exists(), full_output
    alpha_updated = json.loads(alpha_updated_path.read_text(encoding="utf-8"))
    assert alpha_updated["source_registry"] == "clawhub"
    assert alpha_updated["source_slug"] == "owner-alpha/agent-alpha"


def test_feature85_deprecated_paths_warn_and_remain_compatible(tmp_path: Path) -> None:
    agent_dir = tmp_path / "feature85-legacy-run-agent"
    _write_minimal_python_agent(agent_dir)

    legacy_run = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "run",
            str(agent_dir),
            "hello",
            "--experimental-openclaw-adapter",
        ],
        capture_output=True,
        text=True,
    )
    legacy_run_output = f"{legacy_run.stdout}\n{legacy_run.stderr}"
    assert legacy_run.returncode == 0, legacy_run_output
    assert "legacy-run-ok hello" in legacy_run_output
    assert "category=openclaw_bridge_path_deprecated" in legacy_run_output
    assert "path=run_experimental_openclaw_adapter" in legacy_run_output
    assert "replacement=kinnoo run <agent-dir> '<prompt>' [--thinking <level>] [--json]" in legacy_run_output

    registry_root = tmp_path / "registry-sandbox"
    fixture_path = tmp_path / "clawhub-sync-fixture.json"
    fixture_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "slug": "owner-alpha/agent-alpha",
                        "version": "1.0.0",
                        "source_url": "https://clawhub.dev/owner-alpha/agent-alpha",
                        "metadata": {"title": "Agent Alpha"},
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    sync_env = {
        **os.environ,
        "KINNOO_REGISTRY_ROOT": str(registry_root),
        "KINNOO_CLAWHUB_SYNC_FIXTURE": str(fixture_path),
    }
    legacy_sync = subprocess.run(
        [sys.executable, str(CLI_PATH), "sync", "clawhub"],
        capture_output=True,
        text=True,
        env=sync_env,
    )
    legacy_sync_output = f"{legacy_sync.stdout}\n{legacy_sync.stderr}"
    assert legacy_sync.returncode == 0, legacy_sync_output
    assert "category=openclaw_bridge_path_deprecated" in legacy_sync_output
    assert "path=sync_clawhub" in legacy_sync_output
    assert "kinnoo search --openclaw-skill <query> [--json]" in legacy_sync_output
    assert "kinnoo install <agent-name> --openclaw-skill <owner/skill-or-url>" in legacy_sync_output
    assert "source=clawhub mode=incremental created=1 updated=0 skipped=0 failed=0" in legacy_sync_output
