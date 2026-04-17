# [agent] test deprecated: Feature12 CLI registry tests are superseded by feature13 tests.
# def test_publish_cli_usage_and_local_flag(...) -> None:
#     ...
#
# def test_install_remote_success_downloads_and_extracts(...) -> None:
#     ...
#
# def test_install_remote_missing_error_hints_sources(...) -> None:
#     ...
#
# def test_search_remote_lists_matches_with_source_label(...) -> None:
#     ...
#
# def test_search_default_prefers_local_then_falls_back_remote(...) -> None:
#     ...
#
# def test_list_remote_lists_latest_with_source_label(...) -> None:
#     ...
#
# def test_list_default_prefers_local_then_falls_back_remote(...) -> None:
#     ...
#
# def test_publish_requires_target_and_prints_default_target(...) -> None:
#     ...

from __future__ import annotations

import contextlib
import io
import base64
import json
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import zipfile

from kinnoo.registry import RegistryService
from kinnoo.registry_backends import MockFilesystemRegistryBackend
from tests.helpers import run_command


def _run_registry_command(
	command: str,
	*args: object,
	cwd: Path | str | None = None,
	env: dict[str, str] | None = None,
	input_text: str | None = None,
):
	return run_command(command, *args, cwd=cwd, env=env, input_text=input_text)


def _write_archive(
	archive_root: Path,
	*,
	name: str,
	version: str,
) -> Path:
	archive_path = archive_root / name / version / f"{name}.kno"
	archive_path.parent.mkdir(parents=True, exist_ok=True)

	manifest_text = (
		"\n".join(
			[
				f"name: {name}",
				f"version: {version}",
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
		archive_zip.writestr("run.py", "print('feature56')\n")
		archive_zip.writestr("requirements.txt", "")

	return archive_path


def test_feature56_local_publish_tenant_path(tmp_path: Path) -> None:
	archive_root = tmp_path / "archive"
	registry_root = tmp_path / "registry"
	_write_archive(archive_root, name="tenant-path-agent", version="1.0.0")

	env = {
		**os.environ,
		"KINNOO_ARCHIVE_ROOT": str(archive_root),
		"KINNOO_REGISTRY_ROOT": str(registry_root),
		"KINNOO_TENANT_SLUG": "tenant-alpha",
	}

	publish = _run_registry_command("publish", "tenant-path-agent", "--local", env=env)
	output = f"{publish.stdout}\n{publish.stderr}"
	assert publish.returncode == 0, output

	tenant_archive = (
		registry_root
		/ "tenants"
		/ "tenant-alpha"
		/ "tenant-path-agent"
		/ "1.0.0"
		/ "tenant-path-agent.kno"
	)
	tenant_metadata = tenant_archive.parent / "manifest-metadata.json"

	assert tenant_archive.exists()
	assert tenant_metadata.exists()


def test_feature61_login_interactive_and_noninteractive(tmp_path: Path) -> None:
	accepted = {
		("interactive@example.com", "interactive-pass"): "team-interactive",
		("cli@example.com", "cli-pass"): "platform-ops",
	}

	server = _AuthTokenTestServer(accepted_credentials=accepted)
	server.start()
	try:
		env = {
			**os.environ,
			"HOME": str(tmp_path / "home"),
			"KINNOO_REGISTRY_URL": server.base_url,
		}

		interactive = _run_registry_command(
			"login",
			input_text="interactive@example.com\ninteractive-pass\n",
			env=env,
		)
		interactive_output = f"{interactive.stdout}\n{interactive.stderr}"
		assert interactive.returncode == 0, interactive_output
		assert "Login successful." in interactive_output

		config_path = Path(env["HOME"]) / ".kinnoo" / "config.yaml"
		assert config_path.exists()
		first_config = config_path.read_text(encoding="utf-8")
		assert f"registry_url: '{server.base_url}'" in first_config
		assert "tenant_slug: 'team-interactive'" in first_config
		assert "tenant_slug: 'interactive'" not in first_config

		noninteractive = _run_registry_command(
			"login",
			"--email",
			"cli@example.com",
			"--password",
			"cli-pass",
			env=env,
		)
		noninteractive_output = f"{noninteractive.stdout}\n{noninteractive.stderr}"
		assert noninteractive.returncode == 0, noninteractive_output
		assert "Login successful." in noninteractive_output

		second_config = config_path.read_text(encoding="utf-8")
		assert "tenant_slug: 'platform-ops'" in second_config
		assert "tenant_slug: 'cli'" not in second_config
	finally:
		server.stop()


def test_feature61_logout_and_auth_precedence(tmp_path: Path) -> None:
	archive_root = tmp_path / "archive"
	_write_archive(archive_root, name="feature61-agent", version="1.0.0")

	home_dir = tmp_path / "home"
	config_path = home_dir / ".kinnoo" / "config.yaml"
	config_path.parent.mkdir(parents=True, exist_ok=True)

	server = _AuthPublishTestServer(accepted_publish_token="env-token")
	server.start()
	try:
		config_path.write_text(
			"\n".join(
				[
					f"registry_url: '{server.base_url}'",
					"registry_token: 'config-token'",
					"tenant_slug: 'config-tenant'",
				]
			)
			+ "\n",
			encoding="utf-8",
		)

		base_env = {
			**os.environ,
			"HOME": str(home_dir),
			"KINNOO_ARCHIVE_ROOT": str(archive_root),
		}

		logout = _run_registry_command("logout", env=base_env, cwd=tmp_path)
		logout_output = f"{logout.stdout}\n{logout.stderr}"
		assert logout.returncode == 0, logout_output
		assert "Logout successful." in logout_output

		post_logout = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
		assert "registry_token" not in post_logout
		assert "tenant_slug" not in post_logout

		env_without_auth = {
			**base_env,
			"KINNOO_REGISTRY_URL": server.base_url,
		}
		publish_without_auth = _run_registry_command(
			"publish",
			"feature61-agent",
			"--remote",
			env=env_without_auth,
			cwd=tmp_path,
		)
		missing_auth_output = f"{publish_without_auth.stdout}\n{publish_without_auth.stderr}"
		assert publish_without_auth.returncode != 0
		assert "Remote registry configuration incomplete" in missing_auth_output

		env_with_overrides = {
			**env_without_auth,
			"KINNOO_REGISTRY_TOKEN": "env-token",
			"KINNOO_TENANT_SLUG": "env-tenant",
		}
		publish_with_overrides = _run_registry_command(
			"publish",
			"feature61-agent",
			"--remote",
			env=env_with_overrides,
			cwd=tmp_path,
		)
		override_output = f"{publish_with_overrides.stdout}\n{publish_with_overrides.stderr}"
		assert publish_with_overrides.returncode == 0, override_output
		assert "Published feature61-agent==1.0.0 (remote)" in override_output
	finally:
		server.stop()


def test_feature61_publish_toggle_prefers_logged_in_auth_state(tmp_path: Path) -> None:
	archive_root = tmp_path / "archive"
	_write_archive(archive_root, name="feature61-agent", version="1.0.0")

	home_dir = tmp_path / "home"
	config_path = home_dir / ".kinnoo" / "config.yaml"
	config_path.parent.mkdir(parents=True, exist_ok=True)

	server = _AuthPublishTestServer(accepted_publish_token="config-token")
	server.start()
	try:
		config_path.write_text(
			"\n".join(
				[
					f"registry_url: '{server.base_url}'",
					"registry_token: 'config-token'",
					"tenant_slug: 'jerryschen'",
				]
			)
			+ "\n",
			encoding="utf-8",
		)

		(tmp_path / "kinnoo-config.txt").write_text(
			"publish_to_authenticated_registry=true\n",
			encoding="utf-8",
		)

		env = {
			**os.environ,
			"HOME": str(home_dir),
			"KINNOO_ARCHIVE_ROOT": str(archive_root),
		}

		publish_result = _run_registry_command(
			"publish",
			"feature61-agent",
			"--remote",
			env=env,
			cwd=tmp_path,
		)
		publish_output = f"{publish_result.stdout}\n{publish_result.stderr}"
		assert publish_result.returncode == 0, publish_output
		assert "Published feature61-agent==1.0.0 (remote)" in publish_output
	finally:
		server.stop()


def test_feature61_hardened_login_logout_remote_auth_gating(tmp_path: Path) -> None:
	archive_root = tmp_path / "archive"
	_write_archive(archive_root, name="feature61-agent", version="1.0.0")

	server = _RegistryAuthGatingTestServer(
		user_credentials={
			("kinnooteam@gmail.com", "kinnooteam-pass"): "team-kinnoo",
			("admin@example.com", "admin-secret"): "global",
		}
	)
	server.start()
	try:
		home_dir = tmp_path / "home"
		env = {
			**os.environ,
			"HOME": str(home_dir),
			"KINNOO_REGISTRY_URL": server.base_url,
			"KINNOO_ARCHIVE_ROOT": str(archive_root),
		}

		login = _run_registry_command(
			"login",
			"--email",
			"kinnooteam@gmail.com",
			"--password",
			"kinnooteam-pass",
			env=env,
			cwd=tmp_path,
		)
		login_output = f"{login.stdout}\n{login.stderr}"
		assert login.returncode == 0, login_output
		assert "Login successful." in login_output

		config_path = home_dir / ".kinnoo" / "config.yaml"
		config_after_login = config_path.read_text(encoding="utf-8")
		assert "tenant_slug: 'team-kinnoo'" in config_after_login
		assert "tenant_slug: 'kinnooteam'" not in config_after_login

		list_remote = _run_registry_command("list", "--remote", env=env, cwd=tmp_path)
		list_output = f"{list_remote.stdout}\n{list_remote.stderr}"
		assert list_remote.returncode == 0, list_output
		assert "Remote registry agents:" in list_output

		search_remote = _run_registry_command(
			"search", "--remote", "feature61", env=env, cwd=tmp_path
		)
		search_output = f"{search_remote.stdout}\n{search_remote.stderr}"
		assert search_remote.returncode == 0, search_output
		assert "Remote registry search results for: feature61" in search_output

		logout = _run_registry_command("logout", env=env, cwd=tmp_path)
		logout_output = f"{logout.stdout}\n{logout.stderr}"
		assert logout.returncode == 0, logout_output
		assert "Logout successful." in logout_output

		config_after_logout = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
		assert "registry_token" not in config_after_logout
		assert "tenant_slug" not in config_after_logout

		list_after_logout = _run_registry_command("list", "--remote", env=env, cwd=tmp_path)
		list_after_logout_output = f"{list_after_logout.stdout}\n{list_after_logout.stderr}"
		assert list_after_logout.returncode != 0
		assert "Remote registry authentication is missing" in list_after_logout_output

		search_after_logout = _run_registry_command(
			"search", "--remote", "feature61", env=env, cwd=tmp_path
		)
		search_after_logout_output = f"{search_after_logout.stdout}\n{search_after_logout.stderr}"
		assert search_after_logout.returncode != 0
		assert "Remote registry authentication is missing" in search_after_logout_output

		no_registry_home = tmp_path / "home-no-registry"
		no_registry_env = {
			**os.environ,
			"HOME": str(no_registry_home),
			"KINNOO_ARCHIVE_ROOT": str(archive_root),
		}

		list_no_registry = _run_registry_command(
			"list", "--remote", env=no_registry_env, cwd=tmp_path
		)
		list_no_registry_output = f"{list_no_registry.stdout}\n{list_no_registry.stderr}"
		assert list_no_registry.returncode != 0
		assert "Remote mode requires a registry URL" in list_no_registry_output
		assert "does not fall back to local mock storage" in list_no_registry_output

		search_no_registry = _run_registry_command(
			"search", "--remote", "feature61", env=no_registry_env, cwd=tmp_path
		)
		search_no_registry_output = f"{search_no_registry.stdout}\n{search_no_registry.stderr}"
		assert search_no_registry.returncode != 0
		assert "Remote mode requires a registry URL" in search_no_registry_output
		assert "does not fall back to local mock storage" in search_no_registry_output

		(tmp_path / "kinnoo-config.txt").write_text(
			"publish_to_authenticated_registry=true\n",
			encoding="utf-8",
		)
		publish_env = {
			**env,
			"REGISTRY_ADMIN_EMAIL": "admin@example.com",
			"REGISTRY_ADMIN_PASSWORD": "admin-secret",
		}
		publish_with_admin_bypass = _run_registry_command(
			"publish",
			"feature61-agent",
			"--remote",
			env=publish_env,
			cwd=tmp_path,
		)
		publish_output = f"{publish_with_admin_bypass.stdout}\n{publish_with_admin_bypass.stderr}"
		assert publish_with_admin_bypass.returncode == 0, publish_output
		assert "Published feature61-agent==1.0.0 (remote)" in publish_output
	finally:
		server.stop()


def test_publish_preserves_all_versions(tmp_path: Path) -> None:
	archive_root = tmp_path / "archive"
	registry_root = tmp_path / "registry"

	_write_archive(archive_root, name="feature115-versioned-agent", version="1.0.0")
	publish_v1_env = {
		**os.environ,
		"KINNOO_ARCHIVE_ROOT": str(archive_root),
		"KINNOO_REGISTRY_ROOT": str(registry_root),
	}
	publish_v1 = _run_registry_command(
		"publish",
		"feature115-versioned-agent",
		"--local",
		env=publish_v1_env,
		cwd=tmp_path,
	)
	publish_v1_output = f"{publish_v1.stdout}\n{publish_v1.stderr}"
	assert publish_v1.returncode == 0, publish_v1_output

	_write_archive(archive_root, name="feature115-versioned-agent", version="1.1.0")
	publish_v2 = _run_registry_command(
		"publish",
		"feature115-versioned-agent",
		"--local",
		env=publish_v1_env,
		cwd=tmp_path,
	)
	publish_v2_output = f"{publish_v2.stdout}\n{publish_v2.stderr}"
	assert publish_v2.returncode == 0, publish_v2_output

	v1_target_line = next(
		(line for line in publish_v1_output.splitlines() if line.startswith("Target registry path: ")),
		None,
	)
	v2_target_line = next(
		(line for line in publish_v2_output.splitlines() if line.startswith("Target registry path: ")),
		None,
	)
	assert v1_target_line is not None, publish_v1_output
	assert v2_target_line is not None, publish_v2_output

	v1_registry_archive = Path(v1_target_line.replace("Target registry path: ", "", 1).strip())
	v2_registry_archive = Path(v2_target_line.replace("Target registry path: ", "", 1).strip())
	assert v1_registry_archive.exists()
	assert v2_registry_archive.exists()

	list_result = _run_registry_command("list", "--local", env=publish_v1_env, cwd=tmp_path)
	list_output = f"{list_result.stdout}\n{list_result.stderr}"
	assert list_result.returncode == 0, list_output
	assert "feature115-versioned-agent | latest: 1.1.0" in list_output

	search_result = _run_registry_command(
		"search",
		"--local",
		"feature115-versioned-agent",
		env=publish_v1_env,
		cwd=tmp_path,
	)
	search_output = f"{search_result.stdout}\n{search_result.stderr}"
	assert search_result.returncode == 0, search_output
	assert "feature115-versioned-agent | latest: 1.1.0" in search_output


def test_feature63_mirror_attribution_and_idempotency(tmp_path: Path) -> None:
	registry_root = tmp_path / "registry"
	service = RegistryService(backend=MockFilesystemRegistryBackend(root=registry_root))

	service.upsert_clawhub_mirror_record(
		agent_slug="weather/weather-skill",
		source_version="1.2.3",
		source_url="https://clawhub.ai/skills/weather/weather-skill",
		synced_at="2026-03-29T01:00:00Z",
		metadata={"description": "Weather skill"},
	)
	service.upsert_clawhub_mirror_record(
		agent_slug="weather/weather-skill",
		source_version="1.2.3",
		source_url="https://clawhub.ai/skills/weather/weather-skill",
		synced_at="2026-03-29T02:00:00Z",
		metadata={"description": "Weather skill updated sync"},
	)
	service.upsert_clawhub_mirror_record(
		agent_slug="weather/weather-skill",
		source_version="1.2.4",
		source_url="https://clawhub.ai/skills/weather/weather-skill",
		synced_at="2026-03-29T03:00:00Z",
		metadata={"description": "Weather skill v1.2.4"},
	)

	records = service.list_clawhub_mirror_records()
	assert len(records) == 2
	assert [record.source_version for record in records] == ["1.2.3", "1.2.4"]

	from src.kinnoo import search_command
	from src.kinnoo.config import RegistryConfig
	from src.kinnoo.inspect_command import inspect_target

	original_load_registry_config = search_command.load_registry_config
	original_remote_client = search_command.RemoteRegistryClient
	original_registry_service = search_command.RegistryService

	class _MirrorRemoteClientStub:
		def __init__(self, *, base_url: str, token: str, tenant_slug: str) -> None:
			del base_url, token, tenant_slug

		def search_agents(self, *, query: str) -> list[object]:
			return service.search_agents(query=query)

		def list_clawhub_mirror_records(self) -> list[object]:
			return service.list_clawhub_mirror_records()

	search_command.load_registry_config = lambda: RegistryConfig(
		registry_url="https://registry.example.test",
		registry_token="token",
		tenant_slug="tenant-alpha",
	)
	search_command.RemoteRegistryClient = _MirrorRemoteClientStub
	search_command.RegistryService = RegistryService
	try:
		search_stdout = io.StringIO()
		search_stderr = io.StringIO()
		with contextlib.redirect_stdout(search_stdout), contextlib.redirect_stderr(search_stderr):
			search_code = search_command.search_agents(query="weather", source="remote")
		search_output = search_stdout.getvalue() + search_stderr.getvalue()
		assert search_code == 0, search_output
		assert "source: clawhub (mirrored)" in search_output
		assert "synced_at: 2026-03-29T03:00:00Z" in search_output

		namespace_stdout = io.StringIO()
		namespace_stderr = io.StringIO()
		with contextlib.redirect_stdout(namespace_stdout), contextlib.redirect_stderr(namespace_stderr):
			namespace_code = search_command.search_agents(query="clawhub", source="remote")
		namespace_output = namespace_stdout.getvalue() + namespace_stderr.getvalue()
		assert namespace_code == 0, namespace_output
		assert "source: clawhub (mirrored)" in namespace_output

		inspect_stdout = io.StringIO()
		inspect_stderr = io.StringIO()
		with contextlib.redirect_stdout(inspect_stdout), contextlib.redirect_stderr(inspect_stderr):
			inspect_code = inspect_target("clawhub:weather/weather-skill")
		inspect_output = inspect_stdout.getvalue() + inspect_stderr.getvalue()
		assert inspect_code == 0, inspect_output
		assert "Source: ClawHub (mirrored)" in inspect_output
		assert "Last Synced At: 2026-03-29T03:00:00Z" in inspect_output
	finally:
		search_command.load_registry_config = original_load_registry_config
		search_command.RemoteRegistryClient = original_remote_client
		search_command.RegistryService = original_registry_service


def test_feature71_strict_publish_and_docs(tmp_path: Path) -> None:
	from src.kinnoo.signing import create_detached_signature_artifacts, generate_ed25519_keypair

	archive_root = tmp_path / "archive"
	registry_root = tmp_path / "registry"

	manifest_text = (
		"name: strict-publish-agent\n"
		"version: 1.0.0\n"
		"entrypoint: run.py\n"
		"runtime:\n"
		"  language: python\n"
		"  version: \">=3.10\"\n"
		"  type: one-shot\n"
		"dependencies: []\n"
		"inputs:\n"
		"  type: text\n"
		"outputs:\n"
		"  type: text\n"
	)

	unsigned_archive = archive_root / "strict-publish-agent" / "1.0.0" / "strict-publish-agent.kno"
	unsigned_archive.parent.mkdir(parents=True, exist_ok=True)
	with zipfile.ZipFile(unsigned_archive, "w") as archive_zip:
		archive_zip.writestr("kinnoo.yaml", manifest_text)
		archive_zip.writestr("run.py", "print('strict publish')\n")

	env = {
		**os.environ,
		"KINNOO_ARCHIVE_ROOT": str(archive_root),
		"KINNOO_REGISTRY_ROOT": str(registry_root),
		"KINNOO_TENANT_SLUG": "tenant-strict",
	}

	unsigned_publish = _run_registry_command(
		"publish", "strict-publish-agent", "--local", "--strict", env=env
	)
	unsigned_output = f"{unsigned_publish.stdout}\n{unsigned_publish.stderr}"
	assert unsigned_publish.returncode != 0
	assert "Strict publish requires valid signature metadata" in unsigned_output

	private_key_path = tmp_path / "strict-publish-private.pem"
	public_key_path = tmp_path / "strict-publish-public.pem"
	generate_ed25519_keypair(private_key_path=private_key_path, public_key_path=public_key_path)
	create_detached_signature_artifacts(
		archive_path=unsigned_archive,
		private_key_path=private_key_path,
	)

	signed_publish = _run_registry_command(
		"publish", "strict-publish-agent", "--local", "--strict", env=env
	)
	signed_output = f"{signed_publish.stdout}\n{signed_publish.stderr}"
	assert signed_publish.returncode == 0, signed_output
	assert "Published strict-publish-agent==1.0.0 (local)" in signed_output

	repo_root = Path(__file__).resolve().parents[1]
	workflow_text = (repo_root / ".github" / "workflows" / "kinnoo-publish.yml").read_text(encoding="utf-8")
	readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
	combined_docs = f"{workflow_text}\n{readme_text}"
	assert "--strict" in combined_docs
	assert "KINNOO_CI_STRICT_MODE" in combined_docs


def test_feature84_skill_search_delegation_and_json_passthrough(tmp_path: Path) -> None:
	fake_bin = tmp_path / "feature84-openclaw-search-bin"
	fake_bin.mkdir(parents=True, exist_ok=True)
	invocation_log = tmp_path / "feature84-openclaw-search.log"

	openclaw_script = fake_bin / "openclaw"
	openclaw_script.write_text(
		"#!/bin/sh\n"
		"if [ -n \"$KINNOO_TEST_OPENCLAW_SEARCH_LOG\" ]; then\n"
		"  printf '%s\\n' \"$*\" >> \"$KINNOO_TEST_OPENCLAW_SEARCH_LOG\"\n"
		"fi\n"
		"if [ \"$1\" = \"--version\" ]; then\n"
		"  echo openclaw 2026.3.31\n"
		"  exit 0\n"
		"fi\n"
		"if [ \"$1\" = \"gateway\" ] && [ \"$2\" = \"status\" ] && [ \"$3\" = \"--require-rpc\" ]; then\n"
		"  echo gateway healthy\n"
		"  exit 0\n"
		"fi\n"
		"if [ \"$1\" = \"skills\" ] && [ \"$2\" = \"search\" ]; then\n"
		"  if [ \"$4\" = \"--json\" ]; then\n"
		"    echo '[{\"slug\":\"owner/skill\"}]'\n"
		"    exit 0\n"
		"  fi\n"
		"  echo owner/skill\n"
		"  exit 0\n"
		"fi\n"
		"echo unsupported invocation >&2\n"
		"exit 2\n",
		encoding="utf-8",
	)
	openclaw_script.chmod(0o755)

	env = {
		**os.environ,
		"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
		"KINNOO_TEST_OPENCLAW_SEARCH_LOG": str(invocation_log),
	}

	default_result = _run_registry_command("search", "--openclaw-skill", "weather", env=env)
	default_output = f"{default_result.stdout}\n{default_result.stderr}"
	assert default_result.returncode == 0, default_output
	assert "owner/skill" in default_output

	json_result = _run_registry_command(
		"search", "--openclaw-skill", "--json", "weather", env=env
	)
	json_output = f"{json_result.stdout}\n{json_result.stderr}"
	assert json_result.returncode == 0, json_output
	assert '[{"slug":"owner/skill"}]' in json_result.stdout

	invocations = invocation_log.read_text(encoding="utf-8")
	assert "skills search weather" in invocations
	assert "skills search weather --json" in invocations


def test_feature84_skill_search_preflight_empty_and_error_guidance(tmp_path: Path) -> None:
	missing_cli_env = {**os.environ, "PATH": ""}
	missing_cli_result = _run_registry_command(
		"search", "--openclaw-skill", "weather", env=missing_cli_env
	)
	missing_cli_output = f"{missing_cli_result.stdout}\n{missing_cli_result.stderr}"
	assert missing_cli_result.returncode != 0
	assert "category=openclaw_cli_missing" in missing_cli_output

	fake_bin = tmp_path / "feature84-openclaw-guidance-bin"
	fake_bin.mkdir(parents=True, exist_ok=True)
	openclaw_script = fake_bin / "openclaw"
	openclaw_script.write_text(
		"#!/bin/sh\n"
		"if [ \"$1\" = \"--version\" ]; then\n"
		"  echo openclaw 2026.3.31\n"
		"  exit 0\n"
		"fi\n"
		"if [ \"$1\" = \"gateway\" ] && [ \"$2\" = \"status\" ] && [ \"$3\" = \"--require-rpc\" ]; then\n"
		"  echo gateway healthy\n"
		"  exit 0\n"
		"fi\n"
		"if [ \"$1\" = \"skills\" ] && [ \"$2\" = \"search\" ]; then\n"
		"  if [ \"$KINNOO_TEST_OPENCLAW_SEARCH_MODE\" = \"empty\" ]; then\n"
		"    echo '[]'\n"
		"    exit 0\n"
		"  fi\n"
		"  if [ \"$KINNOO_TEST_OPENCLAW_SEARCH_MODE\" = \"error\" ]; then\n"
		"    echo upstream search failed >&2\n"
		"    exit 4\n"
		"  fi\n"
		"  echo '[{\"slug\":\"owner/skill\"}]'\n"
		"  exit 0\n"
		"fi\n"
		"echo unsupported invocation >&2\n"
		"exit 2\n",
		encoding="utf-8",
	)
	openclaw_script.chmod(0o755)

	empty_env = {
		**os.environ,
		"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
		"KINNOO_TEST_OPENCLAW_SEARCH_MODE": "empty",
	}
	empty_result = _run_registry_command("search", "--openclaw-skill", "weather", env=empty_env)
	empty_output = f"{empty_result.stdout}\n{empty_result.stderr}"
	assert empty_result.returncode == 0, empty_output
	assert "No OpenClaw skill results found for query: weather" in empty_output

	empty_json_result = _run_registry_command(
		"search", "--openclaw-skill", "--json", "weather", env=empty_env
	)
	empty_json_output = f"{empty_json_result.stdout}\n{empty_json_result.stderr}"
	assert empty_json_result.returncode == 0, empty_json_output
	assert "[]" in empty_json_result.stdout

	error_env = dict(empty_env)
	error_env["KINNOO_TEST_OPENCLAW_SEARCH_MODE"] = "error"
	error_result = _run_registry_command("search", "--openclaw-skill", "weather", env=error_env)
	error_output = f"{error_result.stdout}\n{error_result.stderr}"
	assert error_result.returncode != 0
	assert "category=openclaw_skill_search_nonzero_exit" in error_output


def test_search_openclaw_skills_removed(tmp_path: Path) -> None:
	result = _run_registry_command("search", "--openclaw-skills", "weather")
	output = f"{result.stdout}\n{result.stderr}"
	assert result.returncode != 0
	assert "unrecognized arguments" in output
	assert "--openclaw-skills" in output

	help_result = _run_registry_command("search", "-h")
	help_output = f"{help_result.stdout}\n{help_result.stderr}"
	assert help_result.returncode == 0
	assert "--openclaw-skills" not in help_output
	assert "--openclaw-skill" not in help_output


def test_search_json_output(tmp_path: Path) -> None:
	archive_root = tmp_path / "archive"
	_write_archive(archive_root, name="task477-json-agent", version="1.0.0")

	env = {
		**os.environ,
		"KINNOO_ARCHIVE_ROOT": str(archive_root),
	}

	result = _run_registry_command("search", "--local", "--json", "task477", env=env)
	output = f"{result.stdout}\n{result.stderr}"
	assert result.returncode == 0, output

	payload = json.loads(result.stdout.strip())
	assert payload["source"] == "local"
	assert payload["query"] == "task477"
	assert isinstance(payload["results"], list)
	assert payload["results"]
	assert payload["results"][0]["name"] == "task477-json-agent"


def test_list_json_output(tmp_path: Path) -> None:
	archive_root = tmp_path / "archive"
	_write_archive(archive_root, name="task478-json-agent", version="1.0.0")

	env = {
		**os.environ,
		"KINNOO_ARCHIVE_ROOT": str(archive_root),
	}

	result = _run_registry_command("list", "--local", "--json", env=env)
	output = f"{result.stdout}\n{result.stderr}"
	assert result.returncode == 0, output

	payload = json.loads(result.stdout.strip())
	assert payload["source"] == "local"
	assert isinstance(payload["results"], list)
	assert payload["results"]
	assert payload["results"][0]["name"] == "task478-json-agent"


class _AuthTokenTestServer:
	def __init__(self, *, accepted_credentials: dict[tuple[str, str], str]) -> None:
		self._accepted_credentials = accepted_credentials
		self._server = ThreadingHTTPServer(("127.0.0.1", 0), _make_auth_handler(accepted_credentials))
		self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

	@property
	def base_url(self) -> str:
		host, port = self._server.server_address
		return f"http://{host}:{port}"

	def start(self) -> None:
		self._thread.start()

	def stop(self) -> None:
		self._server.shutdown()
		self._server.server_close()
		self._thread.join(timeout=2)


class _AuthPublishTestServer:
	def __init__(self, *, accepted_publish_token: str) -> None:
		self._server = ThreadingHTTPServer(
			("127.0.0.1", 0),
			_make_auth_publish_handler(accepted_publish_token=accepted_publish_token),
		)
		self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

	@property
	def base_url(self) -> str:
		host, port = self._server.server_address
		return f"http://{host}:{port}"

	def start(self) -> None:
		self._thread.start()

	def stop(self) -> None:
		self._server.shutdown()
		self._server.server_close()
		self._thread.join(timeout=2)


def _make_auth_handler(
	accepted_credentials: dict[tuple[str, str], str],
) -> type[BaseHTTPRequestHandler]:
	class _AuthHandler(BaseHTTPRequestHandler):
		def do_POST(self) -> None:  # noqa: N802
			if self.path != "/api/auth/token":
				self._write_json(404, {"error": "not found"})
				return

			content_length = int(self.headers.get("Content-Length", "0"))
			payload_text = self.rfile.read(content_length).decode("utf-8")
			try:
				payload = json.loads(payload_text)
			except json.JSONDecodeError:
				self._write_json(400, {"error": "invalid JSON"})
				return

			username = str(payload.get("username", ""))
			password = str(payload.get("password", ""))
			if "tenant_slug" in payload:
				self._write_json(400, {"error": "tenant_slug should not be required for login"})
				return

			tenant_slug = accepted_credentials.get((username, password))
			if tenant_slug is None:
				self._write_json(401, {"error": {"message": "invalid username or password"}})
				return

			token = _make_test_jwt(tenant_slug)
			self._write_json(
				200,
				{
					"access_token": token,
					"token_type": "Bearer",
					"expires_in": 3600,
				},
			)

		def log_message(self, format: str, *args: object) -> None:  # noqa: A003
			del format, args

		def _write_json(self, status_code: int, payload: dict[str, object]) -> None:
			encoded = json.dumps(payload).encode("utf-8")
			self.send_response(status_code)
			self.send_header("Content-Type", "application/json")
			self.send_header("Content-Length", str(len(encoded)))
			self.end_headers()
			self.wfile.write(encoded)

	return _AuthHandler


class _RegistryAuthGatingTestServer:
	def __init__(self, *, user_credentials: dict[tuple[str, str], str]) -> None:
		self._server = ThreadingHTTPServer(
			("127.0.0.1", 0),
			_make_registry_auth_gating_handler(user_credentials=user_credentials),
		)
		self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

	@property
	def base_url(self) -> str:
		host, port = self._server.server_address
		return f"http://{host}:{port}"

	def start(self) -> None:
		self._thread.start()

	def stop(self) -> None:
		self._server.shutdown()
		self._server.server_close()
		self._thread.join(timeout=2)


def _make_registry_auth_gating_handler(
	*,
	user_credentials: dict[tuple[str, str], str],
) -> type[BaseHTTPRequestHandler]:
	issued_tokens: set[str] = set()

	class _RegistryAuthGatingHandler(BaseHTTPRequestHandler):
		def do_POST(self) -> None:  # noqa: N802
			if self.path == "/api/auth/token":
				self._handle_auth_token()
				return

			if self.path == "/api/publish":
				self._handle_publish()
				return

			self._write_json(404, {"error": "not found"})

		def do_GET(self) -> None:  # noqa: N802
			if self.path.startswith("/api/agents"):
				self._require_auth_or_401()
				self._write_json(
					200,
					{
						"items": [
							{
								"name": "feature61-agent",
								"latest_version": "1.0.0",
								"description": "feature61 remote fixture",
							}
						]
					},
				)
				return

			if self.path.startswith("/api/search"):
				self._require_auth_or_401()
				self._write_json(
					200,
					{
						"items": [
							{
								"name": "feature61-agent",
								"latest_version": "1.0.0",
								"description": "feature61 remote fixture",
							}
						]
					},
				)
				return

			self._write_json(404, {"error": "not found"})

		def log_message(self, format: str, *args: object) -> None:  # noqa: A003
			del format, args

		def _handle_auth_token(self) -> None:
			content_length = int(self.headers.get("Content-Length", "0"))
			payload_text = self.rfile.read(content_length).decode("utf-8")
			try:
				payload = json.loads(payload_text)
			except json.JSONDecodeError:
				self._write_json(400, {"error": "invalid JSON"})
				return

			username = str(payload.get("username", ""))
			password = str(payload.get("password", ""))
			tenant_slug = user_credentials.get((username, password))
			if tenant_slug is None:
				self._write_json(401, {"error": "invalid username or password"})
				return

			requested_tenant = payload.get("tenant_slug")
			if isinstance(requested_tenant, str) and requested_tenant.strip():
				tenant_slug = requested_tenant.strip()

			token = _make_test_jwt(tenant_slug)
			issued_tokens.add(token)
			self._write_json(
				200,
				{
					"access_token": token,
					"token_type": "Bearer",
					"expires_in": 3600,
				},
			)

		def _handle_publish(self) -> None:
			if not self._require_auth_or_401():
				return

			content_length = int(self.headers.get("Content-Length", "0"))
			_ = self.rfile.read(content_length)
			self._write_json(200, {"archive_path": "remote://feature61-agent/1.0.0"})

		def _require_auth_or_401(self) -> bool:
			authorization = self.headers.get("Authorization", "")
			if not authorization.startswith("Bearer "):
				self._write_json(401, {"error": "unauthorized"})
				return False
			token = authorization.split(" ", 1)[1].strip()
			if token not in issued_tokens:
				self._write_json(401, {"error": "unauthorized"})
				return False
			return True

		def _write_json(self, status_code: int, payload: dict[str, object]) -> None:
			encoded = json.dumps(payload).encode("utf-8")
			self.send_response(status_code)
			self.send_header("Content-Type", "application/json")
			self.send_header("Content-Length", str(len(encoded)))
			self.end_headers()
			self.wfile.write(encoded)

	return _RegistryAuthGatingHandler


def _make_test_jwt(tenant_slug: str) -> str:
	header_segment = _base64url_json({"alg": "none", "typ": "JWT"})
	payload_segment = _base64url_json({"tenant_slug": tenant_slug})
	return f"{header_segment}.{payload_segment}.signature"


def _base64url_json(payload: dict[str, str]) -> str:
	encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
	return encoded.decode("utf-8").rstrip("=")


def _make_auth_publish_handler(*, accepted_publish_token: str) -> type[BaseHTTPRequestHandler]:
	class _AuthPublishHandler(BaseHTTPRequestHandler):
		def do_POST(self) -> None:  # noqa: N802
			if self.path != "/api/publish":
				self._write_json(404, {"error": "not found"})
				return

			authorization = self.headers.get("Authorization", "")
			expected = f"Bearer {accepted_publish_token}"
			if authorization != expected:
				self._write_json(401, {"error": "unauthorized"})
				return

			content_length = int(self.headers.get("Content-Length", "0"))
			_ = self.rfile.read(content_length)
			self._write_json(200, {"archive_path": "remote://feature61-agent/1.0.0"})

		def log_message(self, format: str, *args: object) -> None:  # noqa: A003
			del format, args

		def _write_json(self, status_code: int, payload: dict[str, object]) -> None:
			encoded = json.dumps(payload).encode("utf-8")
			self.send_response(status_code)
			self.send_header("Content-Type", "application/json")
			self.send_header("Content-Length", str(len(encoded)))
			self.end_headers()
			self.wfile.write(encoded)

	return _AuthPublishHandler
