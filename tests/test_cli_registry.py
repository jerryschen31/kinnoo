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
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import zipfile

from kinnoo.registry import RegistryService
from kinnoo.registry_backends import MockFilesystemRegistryBackend


CLI_PATH = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"


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

	publish = subprocess.run(
		[sys.executable, str(CLI_PATH), "publish", "tenant-path-agent", "--local"],
		capture_output=True,
		text=True,
		env=env,
	)
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
		("interactive@example.com", "interactive-pass", "tenant-interactive"): "token-interactive",
		("cli@example.com", "cli-pass", "tenant-cli"): "token-cli",
	}

	server = _AuthTokenTestServer(accepted_credentials=accepted)
	server.start()
	try:
		env = {
			**os.environ,
			"HOME": str(tmp_path / "home"),
		}

		interactive = subprocess.run(
			[
				sys.executable,
				str(CLI_PATH),
				"login",
				"--registry",
				server.base_url,
				"--tenant",
				"tenant-interactive",
			],
			input="interactive@example.com\ninteractive-pass\n",
			capture_output=True,
			text=True,
			env=env,
		)
		interactive_output = f"{interactive.stdout}\n{interactive.stderr}"
		assert interactive.returncode == 0, interactive_output
		assert "Login successful." in interactive_output

		config_path = Path(env["HOME"]) / ".kinnoo" / "config.yaml"
		assert config_path.exists()
		first_config = config_path.read_text(encoding="utf-8")
		assert "registry_url: '" in first_config
		assert "registry_token: 'token-interactive'" in first_config
		assert "tenant_slug: 'tenant-interactive'" in first_config

		noninteractive = subprocess.run(
			[
				sys.executable,
				str(CLI_PATH),
				"login",
				"--registry",
				server.base_url,
				"--tenant",
				"tenant-cli",
				"--email",
				"cli@example.com",
				"--password",
				"cli-pass",
			],
			capture_output=True,
			text=True,
			env=env,
		)
		noninteractive_output = f"{noninteractive.stdout}\n{noninteractive.stderr}"
		assert noninteractive.returncode == 0, noninteractive_output
		assert "Login successful." in noninteractive_output

		second_config = config_path.read_text(encoding="utf-8")
		assert "registry_token: 'token-cli'" in second_config
		assert "tenant_slug: 'tenant-cli'" in second_config
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

		logout = subprocess.run(
			[sys.executable, str(CLI_PATH), "logout"],
			capture_output=True,
			text=True,
			env=base_env,
			cwd=tmp_path,
		)
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
		publish_without_auth = subprocess.run(
			[sys.executable, str(CLI_PATH), "publish", "feature61-agent", "--remote"],
			capture_output=True,
			text=True,
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
		publish_with_overrides = subprocess.run(
			[sys.executable, str(CLI_PATH), "publish", "feature61-agent", "--remote"],
			capture_output=True,
			text=True,
			env=env_with_overrides,
			cwd=tmp_path,
		)
		override_output = f"{publish_with_overrides.stdout}\n{publish_with_overrides.stderr}"
		assert publish_with_overrides.returncode == 0, override_output
		assert "Published feature61-agent==1.0.0 (remote)" in override_output
	finally:
		server.stop()


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

	previous_registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
	original_load_registry_config = search_command.load_registry_config
	search_command.load_registry_config = lambda: RegistryConfig(
		registry_url=None,
		registry_token=None,
		tenant_slug=None,
	)
	os.environ["KINNOO_REGISTRY_ROOT"] = str(registry_root)
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
		if previous_registry_root is None:
			os.environ.pop("KINNOO_REGISTRY_ROOT", None)
		else:
			os.environ["KINNOO_REGISTRY_ROOT"] = previous_registry_root


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

	unsigned_publish = subprocess.run(
		[sys.executable, str(CLI_PATH), "publish", "strict-publish-agent", "--local", "--strict"],
		capture_output=True,
		text=True,
		env=env,
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

	signed_publish = subprocess.run(
		[sys.executable, str(CLI_PATH), "publish", "strict-publish-agent", "--local", "--strict"],
		capture_output=True,
		text=True,
		env=env,
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

	default_result = subprocess.run(
		[
			sys.executable,
			str(CLI_PATH),
			"search",
			"--openclaw-skill",
			"weather",
		],
		capture_output=True,
		text=True,
		env=env,
	)
	default_output = f"{default_result.stdout}\n{default_result.stderr}"
	assert default_result.returncode == 0, default_output
	assert "owner/skill" in default_output

	json_result = subprocess.run(
		[
			sys.executable,
			str(CLI_PATH),
			"search",
			"--openclaw-skill",
			"--json",
			"weather",
		],
		capture_output=True,
		text=True,
		env=env,
	)
	json_output = f"{json_result.stdout}\n{json_result.stderr}"
	assert json_result.returncode == 0, json_output
	assert '[{"slug":"owner/skill"}]' in json_result.stdout

	invocations = invocation_log.read_text(encoding="utf-8")
	assert "skills search weather" in invocations
	assert "skills search weather --json" in invocations


class _AuthTokenTestServer:
	def __init__(self, *, accepted_credentials: dict[tuple[str, str, str], str]) -> None:
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
	accepted_credentials: dict[tuple[str, str, str], str],
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
			tenant_slug = str(payload.get("tenant_slug", ""))
			token = accepted_credentials.get((username, password, tenant_slug))
			if token is None:
				self._write_json(401, {"error": {"message": "invalid username or password"}})
				return

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
