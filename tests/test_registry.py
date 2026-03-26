from pathlib import Path
import importlib.util
import json
import sqlite3
import sys
import os
import subprocess
import zipfile

import pytest

from kinnoo.registry import RegistryBackend, RegistryService
from kinnoo.registry_backends import (
	LocalFilesystemRegistryBackend,
	LocalRegistryBackend,
	MockFilesystemRegistryBackend,
)


# [agent] test deprecated: Feature12 registry tests are superseded by feature13 tests.
# def test_registry_backend_contract_and_local_layout(tmp_path: Path) -> None:
#     ...
#
# def test_registry_version_resolution_latest_and_exact(tmp_path: Path) -> None:
#     ...


def test_registry_backend_protocol(tmp_path: Path) -> None:
	"""Feature28 test327: protocol definition and local backend compatibility."""

	required_methods = {"publish", "resolve", "search", "list_agents"}
	protocol_methods = set(getattr(RegistryBackend, "__dict__", {}).keys())
	assert required_methods.issubset(protocol_methods)

	backend = LocalRegistryBackend(root=tmp_path / "registry")
	assert isinstance(backend, RegistryBackend)

	archive_v1 = tmp_path / "demo-1.0.0.kno"
	archive_v1.write_text("demo-v1", encoding="utf-8")
	archive_v2 = tmp_path / "demo-2.0.0.kno"
	archive_v2.write_text("demo-v2", encoding="utf-8")

	published_v1 = backend.publish(name="demo", version="1.0.0", archive_path=archive_v1)
	published_v2 = backend.publish(name="demo", version="2.0.0", archive_path=archive_v2)

	resolved_latest = backend.resolve(name="demo")
	assert resolved_latest is not None
	assert resolved_latest.version == "2.0.0"
	assert resolved_latest.archive_path == published_v2.archive_path

	resolved_exact = backend.resolve(name="demo", version="1.0.0")
	assert resolved_exact is not None
	assert resolved_exact.archive_path == published_v1.archive_path

	records = backend.search(query="dem")
	assert [record.version for record in records] == ["2.0.0", "1.0.0"]

	agent_summaries = backend.list_agents()
	assert len(agent_summaries) == 1
	assert agent_summaries[0].name == "demo"
	assert agent_summaries[0].latest_version == "2.0.0"

	compat_backend = LocalFilesystemRegistryBackend(root=tmp_path / "registry")
	compat_resolved = compat_backend.resolve(name="demo")
	assert compat_resolved is not None
	assert compat_resolved.version == "2.0.0"


def _load_feature26_filesystem_fixture_module():
	"""Load the feature26 filesystem MCP fixture run module by file path."""
	fixture_path = (
		Path(__file__).resolve().parents[1]
		/ "scratch"
		/ "feature26-filesystem-mcp-server"
		/ "run.py"
	)
	spec = importlib.util.spec_from_file_location("feature26_filesystem_fixture", fixture_path)
	assert spec is not None and spec.loader is not None
	module = importlib.util.module_from_spec(spec)
	sys.modules[spec.name] = module
	spec.loader.exec_module(module)
	return module


def test_feature26_filesystem_permissions_runtime_enforcement(tmp_path: Path) -> None:
	"""Feature26 test238: permission checks hold at helper and MCP tools/call handler levels."""
	fixture = _load_feature26_filesystem_fixture_module()

	default_permissions = fixture.permissions_from_manifest({})
	default_gate = fixture.FilesystemPermissionGate(default_permissions, tmp_path)

	blocked_target = tmp_path / "notes.txt"
	with pytest.raises(fixture.FilesystemPermissionError) as write_error:
		default_gate.assert_allowed("write", blocked_target)
	assert "read-only mode" in str(write_error.value)

	with pytest.raises(fixture.FilesystemPermissionError) as create_error:
		default_gate.assert_allowed("create", blocked_target)
	assert "read-only mode" in str(create_error.value)

	blocked_request = {
		"jsonrpc": "2.0",
		"id": 1,
		"method": "tools/call",
		"params": {
			"name": "filesystem.write",
			"arguments": {"path": str(blocked_target)},
		},
	}
	with pytest.raises(fixture.FilesystemPermissionError) as handler_write_error:
		fixture.handle_mcp_tool_call(blocked_request, default_gate)
	assert "read-only mode" in str(handler_write_error.value)

	allowed_root = tmp_path / "allowed"
	allowed_root.mkdir(parents=True, exist_ok=True)
	allowed_permissions = fixture.permissions_from_manifest(
		{
			"permissions": {
				"read_only": False,
				"allow_write": True,
				"allow_create": True,
				"allowed_paths": ["allowed"],
			}
		}
	)
	allow_gate = fixture.FilesystemPermissionGate(allowed_permissions, tmp_path)

	allowed_target = allowed_root / "doc.txt"
	resolved_target = allow_gate.assert_allowed("write", allowed_target)
	assert resolved_target == allowed_target.resolve()

	created_target = allow_gate.assert_allowed("create", allowed_target)
	assert created_target == allowed_target.resolve()

	allowed_request = {
		"jsonrpc": "2.0",
		"id": 2,
		"method": "tools/call",
		"params": {
			"name": "filesystem.create",
			"arguments": {"path": str(allowed_target)},
		},
	}
	response = fixture.handle_mcp_tool_call(allowed_request, allow_gate)
	assert response["ok"] is True
	assert response["action"] == "create"
	assert response["resolved_path"] == str(allowed_target.resolve())

	outside_target = tmp_path / "outside.txt"
	with pytest.raises(fixture.FilesystemPermissionError) as sandbox_error:
		allow_gate.assert_allowed("write", outside_target)
	assert "allowed_paths sandbox" in str(sandbox_error.value)

	outside_request = {
		"jsonrpc": "2.0",
		"id": 3,
		"method": "tools/call",
		"params": {
			"name": "filesystem.write",
			"arguments": {"path": str(outside_target)},
		},
	}
	with pytest.raises(fixture.FilesystemPermissionError) as handler_sandbox_error:
		fixture.handle_mcp_tool_call(outside_request, allow_gate)
	assert "allowed_paths sandbox" in str(handler_sandbox_error.value)


def test_feature40_registry_publisher_key_association(tmp_path: Path) -> None:
	from src.kinnoo.signing import create_detached_signature_artifacts, generate_ed25519_keypair

	archive_source = tmp_path / "feature40-registry-source.kno"
	manifest_text = (
		"name: feature40-registry-agent\n"
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
	with zipfile.ZipFile(archive_source, "w") as archive_zip:
		archive_zip.writestr("kinnoo.yaml", manifest_text)
		archive_zip.writestr("run.py", "print('feature40-registry-ok')\n")
		archive_zip.writestr("requirements.txt", "")

	key_dir = tmp_path / "publisher-keys"
	key_dir.mkdir(parents=True, exist_ok=True)
	private_key_path = key_dir / "publisher-private.pem"
	public_key_path = key_dir / "publisher-public.pem"
	generate_ed25519_keypair(
		private_key_path=private_key_path,
		public_key_path=public_key_path,
	)
	publisher_public_key = public_key_path.read_text(encoding="utf-8").strip()

	registry_root = tmp_path / "registry-root"
	service = RegistryService(backend=MockFilesystemRegistryBackend(root=registry_root))
	record = service.publish(
		name="feature40-registry-agent",
		version="1.0.0",
		archive_path=archive_source,
		manifest_metadata={
			"name": "feature40-registry-agent",
			"version": "1.0.0",
			"publisher_public_key": publisher_public_key,
		},
	)

	resolved_record = service.resolve(name="feature40-registry-agent", version="1.0.0")
	assert resolved_record is not None
	assert resolved_record.publisher_public_key == publisher_public_key

	create_detached_signature_artifacts(
		archive_path=record.archive_path,
		private_key_path=private_key_path,
	)

	env = dict(os.environ)
	env["KINNOO_REGISTRY_ROOT"] = str(registry_root)

	valid_target = tmp_path / "feature40-registry-valid-install"
	valid_result = subprocess.run(
		[
			sys.executable,
			"src/kinnoo/cli.py",
			"install",
			"feature40-registry-agent==1.0.0",
			str(valid_target),
			"--yes",
		],
		capture_output=True,
		text=True,
		env=env,
	)
	valid_output = f"{valid_result.stdout}\n{valid_result.stderr}"
	assert valid_result.returncode == 0, valid_output
	assert "Archive signature verified" in valid_output

	spoof_private_key_path = key_dir / "spoof-private.pem"
	spoof_public_key_path = key_dir / "spoof-public.pem"
	generate_ed25519_keypair(
		private_key_path=spoof_private_key_path,
		public_key_path=spoof_public_key_path,
	)
	create_detached_signature_artifacts(
		archive_path=record.archive_path,
		private_key_path=spoof_private_key_path,
	)

	spoof_target = tmp_path / "feature40-registry-spoof-install"
	spoof_result = subprocess.run(
		[
			sys.executable,
			"src/kinnoo/cli.py",
			"install",
			"feature40-registry-agent==1.0.0",
			str(spoof_target),
			"--yes",
		],
		capture_output=True,
		text=True,
		env=env,
	)
	spoof_output = f"{spoof_result.stdout}\n{spoof_result.stderr}"
	assert spoof_result.returncode != 0
	assert "public key does not match registry publisher key association" in spoof_output


def test_feature55_login_csrf_passthrough() -> None:
	auth_client_path = Path(__file__).resolve().parents[1] / "web" / "lib" / "auth-client.ts"
	content = auth_client_path.read_text(encoding="utf-8")

	assert 'fetch("/api/login"' in content
	assert 'method: "GET"' in content
	assert 'method: "POST"' in content
	assert 'credentials: "include"' in content
	assert 'form.set("csrf_token", csrfToken)' in content
	assert '"Content-Type": "application/x-www-form-urlencoded"' in content


def test_feature55_session_csrf_forwarding() -> None:
	auth_client_path = Path(__file__).resolve().parents[1] / "web" / "lib" / "auth-client.ts"
	registry_page_path = Path(__file__).resolve().parents[1] / "web" / "app" / "(auth)" / "registry" / "page.tsx"
	auth_client = auth_client_path.read_text(encoding="utf-8")
	registry_page = registry_page_path.read_text(encoding="utf-8")

	assert 'readCookie("kinnoo_csrf")' in auth_client
	assert '"X-CSRF-Token": csrfToken' in auth_client
	assert 'form.set("csrf_token", csrfToken)' in auth_client
	assert 'postWithSessionCsrf("/api/logout")' in auth_client
	assert "logoutWithSessionCsrf" in registry_page


def test_feature55_api_auth_me_contract(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	user = app.state.user_store.create_user(
		username="feature55.user@example.com",
		plaintext_password="feature55-secret",
		role="user",
	)
	session_record, session_cookie = app.state.session_service.create_session(user_id=user.id)
	client.cookies.set(session_cookie.name, session_cookie.value)

	valid = client.get("/api/auth/me")
	assert valid.status_code == 200
	valid_payload = valid.json()
	assert valid_payload["user_id"] == user.id
	assert valid_payload["username"] == user.username
	assert valid_payload["tenant_slug"] == "feature55-user"

	invalid = TestClient(app, base_url="https://testserver")
	missing = invalid.get("/api/auth/me")
	assert missing.status_code == 401
	missing_payload = missing.json()
	assert missing_payload["error"]["code"] == "unauthorized"
	assert missing_payload["error"]["message"]
	assert missing_payload["error"]["request_id"]

	client.cookies.set(session_cookie.name, f"{session_record.session_id}.tampered")
	tampered = client.get("/api/auth/me")
	assert tampered.status_code == 401


def test_feature55_auth_integration_suite(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	# Verify unauthenticated auth-check contract remains 401.
	unauth = client.get("/api/auth/me")
	assert unauth.status_code == 401

	# Validate rewrite/auth-client contracts and no browser token persistence usage.
	next_config = (Path(__file__).resolve().parents[1] / "web" / "next.config.ts").read_text(
		encoding="utf-8"
	)
	auth_client = (Path(__file__).resolve().parents[1] / "web" / "lib" / "auth-client.ts").read_text(
		encoding="utf-8"
	)
	auth_layout = (
		Path(__file__).resolve().parents[1] / "web" / "app" / "(auth)" / "layout.tsx"
	).read_text(encoding="utf-8")

	assert 'source: "/api/:path*"' in next_config
	assert "fetch(\"/api/login\"" in auth_client
	assert "fetch(\"/api/auth/me\"" in auth_client
	assert "localStorage" not in auth_client
	assert "sessionStorage" not in auth_client
	assert "redirect(\"/login\")" in auth_layout


def test_feature56_auth_fallback_paths(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig
	from server.routes.publish import publish_archive

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	user = app.state.user_store.create_user(
		username="tenant-alpha@example.com",
		plaintext_password="feature56-secret",
		role="user",
	)
	session_record, session_cookie = app.state.session_service.create_session(user_id=user.id)
	client.cookies.set(session_cookie.name, session_cookie.value)

	publisher_token = app.state.token_service.issue_token(
		subject="publisher-alpha",
		tenant_slug="tenant-alpha",
		scopes=["registry:read", "registry:publish"],
	)
	reader_token = app.state.token_service.issue_token(
		subject="reader-alpha",
		tenant_slug="tenant-alpha",
		scopes=["registry:read"],
	)

	manifest = (
		"name: feature56-agent\n"
		"version: 1.0.0\n"
		"visibility: private\n"
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
	buff = __import__("io").BytesIO()
	with zipfile.ZipFile(buff, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
		archive.writestr("kinnoo.yaml", manifest)
		archive.writestr("run.py", "print('feature56')\n")
	published = publish_archive(
		authorization_header=f"Bearer {publisher_token}",
		filename="feature56-agent.kno",
		archive_bytes=buff.getvalue(),
		token_service=app.state.token_service,
		storage_backend=app.state.storage_backend,
		metadata_manager=app.state.metadata_manager,
		max_upload_mb=app.state.config.max_upload_mb,
	)
	assert published.status_code == 201

	# Bearer token path works.
	bearer_list = client.get("/api/agents", headers={"Authorization": f"Bearer {reader_token}"})
	assert bearer_list.status_code == 200
	bearer_detail = client.get(
		"/api/agents/tenant-alpha/feature56-agent",
		headers={"Authorization": f"Bearer {reader_token}"},
	)
	assert bearer_detail.status_code == 200
	bearer_search = client.get(
		"/api/search?q=feature56",
		headers={"Authorization": f"Bearer {reader_token}"},
	)
	assert bearer_search.status_code == 200

	# Session-cookie fallback path works without bearer token.
	session_list = client.get("/api/agents")
	assert session_list.status_code == 200
	session_detail = client.get("/api/agents/tenant-alpha/feature56-agent")
	assert session_detail.status_code == 200
	session_search = client.get("/api/search?q=feature56")
	assert session_search.status_code == 200

	# Bearer-first semantics: malformed bearer should fail even with valid session cookie.
	malformed = client.get("/api/agents", headers={"Authorization": "Bearer"})
	assert malformed.status_code == 401

	# No bearer and no session should be unauthorized.
	missing_client = TestClient(app, base_url="https://testserver")
	missing = missing_client.get("/api/agents")
	assert missing.status_code == 401


def test_feature56_admin_bootstrap_secret_safe(tmp_path: Path, monkeypatch) -> None:
	from server.app import create_app
	from server.bootstrap import bootstrap_admin_from_env
	from server.config import ServerConfig
	from server.storage.user_store import UserStore

	secret_password = "feature56-ultra-secret"
	store_root = tmp_path / "storage"
	monkeypatch.setenv("REGISTRY_LOCAL_STORAGE_ROOT", str(store_root))
	monkeypatch.setenv("REGISTRY_ADMIN_EMAIL", "admin-feature56@example.com")
	monkeypatch.setenv("REGISTRY_ADMIN_PASSWORD", secret_password)

	config = ServerConfig.from_env()
	create_app(config=config)
	store = UserStore(store_root / "auth")
	users_after_first = store.list_users()
	assert len(users_after_first) == 1
	assert users_after_first[0].username == "admin-feature56@example.com"
	assert users_after_first[0].role == "admin"

	# Repeated startup must be idempotent (no duplicate admin creation).
	create_app(config=config)
	users_after_second = store.list_users()
	assert len(users_after_second) == 1

	result = bootstrap_admin_from_env(
		store_root=store_root / "auth",
		admin_email="admin-feature56@example.com",
		admin_password=secret_password,
	)
	assert result.username == "admin-feature56@example.com"
	assert secret_password not in result.message
	assert result.temporary_password is None


def test_feature56_integration_suite(tmp_path: Path, monkeypatch) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig
	from server.routes.publish import publish_archive
	from server.storage.user_store import UserStore

	secret_password = "feature56-suite-secret"
	storage_root = tmp_path / "suite-storage"
	monkeypatch.setenv("REGISTRY_LOCAL_STORAGE_ROOT", str(storage_root))
	monkeypatch.setenv("REGISTRY_ADMIN_EMAIL", "suite-admin@example.com")
	monkeypatch.setenv("REGISTRY_ADMIN_PASSWORD", secret_password)

	config = ServerConfig.from_env()
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	store = UserStore(storage_root / "auth")
	admins = [user for user in store.list_users() if user.role == "admin"]
	assert any(user.username == "suite-admin@example.com" for user in admins)

	user = store.create_user(
		username="tenant-alpha@example.com",
		plaintext_password="suite-reader-secret",
		role="user",
	)
	_session_record, session_cookie = app.state.session_service.create_session(user_id=user.id)
	client.cookies.set(session_cookie.name, session_cookie.value)

	publisher_token = app.state.token_service.issue_token(
		subject="publisher-alpha",
		tenant_slug="tenant-alpha",
		scopes=["registry:read", "registry:publish"],
	)

	manifest = (
		"name: suite-feature56-agent\n"
		"version: 1.0.0\n"
		"visibility: private\n"
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
	buff = __import__("io").BytesIO()
	with zipfile.ZipFile(buff, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
		archive.writestr("kinnoo.yaml", manifest)
		archive.writestr("run.py", "print('suite')\n")
	published = publish_archive(
		authorization_header=f"Bearer {publisher_token}",
		filename="suite-feature56-agent.kno",
		archive_bytes=buff.getvalue(),
		token_service=app.state.token_service,
		storage_backend=app.state.storage_backend,
		metadata_manager=app.state.metadata_manager,
		max_upload_mb=app.state.config.max_upload_mb,
	)
	assert published.status_code == 201

	fallback_list = client.get("/api/agents")
	fallback_search = client.get("/api/search?q=suite-feature56")
	assert fallback_list.status_code == 200
	assert fallback_search.status_code == 200

	# Tenant-scoped local publish convention is validated by task313 test fixture.
	cli_registry_test = (Path(__file__).resolve().parents[1] / "tests" / "test_cli_registry.py").read_text(
		encoding="utf-8"
	)
	assert "test_feature56_local_publish_tenant_path" in cli_registry_test
	assert '/ "tenants"' in cli_registry_test


def test_feature57_forwarded_ip_rate_limit_path() -> None:
	from server.middleware import InMemoryRateLimiter, PathRateLimitMiddleware, RateLimitRule

	limiter = InMemoryRateLimiter()
	rules = {"/api/auth/token": RateLimitRule(requests_per_minute=1)}

	class _StubApp:
		async def __call__(self, scope, receive, send):
			await send({"type": "http.response.start", "status": 200, "headers": []})
			await send({"type": "http.response.body", "body": b"ok"})

	middleware = PathRateLimitMiddleware(_StubApp(), limiter=limiter, rules=rules)

	def call_once(*, client_host: str, forwarded_for: str) -> int:
		events = []
		scope = {
			"type": "http",
			"path": "/api/auth/token",
			"client": (client_host, 443),
			"headers": [
				(b"x-forwarded-for", forwarded_for.encode("utf-8")),
				(b"x-request-id", b"feature57-test"),
			],
		}

		async def receive():
			return {"type": "http.request", "body": b"", "more_body": False}

		async def send(message):
			events.append(message)

		import asyncio

		asyncio.run(middleware(scope, receive, send))
		for event in events:
			if event.get("type") == "http.response.start":
				return int(event.get("status", 0))
		return 0

	first_status = call_once(client_host="127.0.0.1", forwarded_for="203.0.113.10")
	second_status = call_once(client_host="127.0.0.2", forwarded_for="203.0.113.10")

	assert first_status == 200
	assert second_status == 429

	middleware_source = (Path(__file__).resolve().parents[1] / "server" / "middleware.py").read_text(
		encoding="utf-8"
	)
	assert "Redis/Upstash" in middleware_source


def test_feature57_hardening_non_regression_suite(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	web_root = Path(__file__).resolve().parents[1] / "web"
	next_config = (web_root / "next.config.ts").read_text(encoding="utf-8")
	web_middleware = (web_root / "middleware.ts").read_text(encoding="utf-8")
	auth_layout_test = (web_root / "__tests__" / "auth-layout.test.tsx").read_text(encoding="utf-8")

	# Env contract expectations for hardening.
	assert "process.env.BACKEND_URL" in next_config
	assert "process.env.NODE_ENV" in web_middleware

	# Header hardening and auth UX coverage should remain present.
	assert "Content-Security-Policy" in web_middleware
	assert "Strict-Transport-Security" in web_middleware
	assert "Loading your registry" in auth_layout_test
	assert "Too many requests" in auth_layout_test

	# Backend core auth flow should still be operational post-hardening.
	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	health = client.get("/health")
	assert health.status_code == 200
	assert health.json()["status"] == "ok"

	login_page = client.get("/login")
	assert login_page.status_code == 200
	assert "csrf_token" in login_page.text

	auth_me_missing = client.get("/api/auth/me")
	assert auth_me_missing.status_code == 401


def test_feature58_register_request_duplicate_safe_generic_response(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	app.state.user_store.create_user(
		username="existing@example.com",
		plaintext_password="existing-password",
		role="user",
	)

	new_response = client.post("/api/auth/register-request", json={"email": "new-user@example.com"})
	existing_response = client.post("/api/auth/register-request", json={"email": "existing@example.com"})

	assert new_response.status_code == 200
	assert existing_response.status_code == 200

	expected_message = "If this email is valid, you'll receive a verification link"
	assert new_response.json() == {"message": expected_message}
	assert existing_response.json() == {"message": expected_message}

	# Only unknown-email requests should dispatch a verification link event.
	assert len(app.state.email_log_sink) == 1
	logged_event = app.state.email_log_sink[0]
	assert logged_event["email"] == "new-user@example.com"
	assert logged_event["verification_link"].startswith("http://localhost:3000/signup/verify?token=")


def test_feature58_register_request_rate_limit(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	for _ in range(5):
		response = client.post("/api/auth/register-request", json={"email": "limit@example.com"})
		assert response.status_code in {200, 429}

	blocked = client.post("/api/auth/register-request", json={"email": "limit@example.com"})
	assert blocked.status_code == 429
	blocked_body = blocked.json()
	assert blocked_body["error"]["code"] == "too_many_requests"
	assert blocked_body["error"]["message"] == "429 too many requests"
	assert blocked_body["error"]["request_id"]


def test_feature58_register_confirm_success_creates_user_tenant_session(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	token = app.state.registration_token_service.issue_token(email="new-owner@example.com")
	response = client.post(
		"/api/auth/register-confirm",
		json={"token": token, "password": "valid-passphrase-123"},
	)
	assert response.status_code == 200
	payload = response.json()
	assert payload["redirect_to"] == "/registry"
	assert payload["tenant_slug"] == "new-owner"
	assert payload["username"] == "new-owner@example.com"

	set_cookie_values = response.headers.get_list("set-cookie")
	joined_cookies = "\n".join(set_cookie_values)
	assert "kinnoo_session=" in joined_cookies
	assert "kinnoo_csrf=" in joined_cookies


def test_feature58_register_confirm_rejects_expired_or_used_token(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient
	import time

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	expired_token = app.state.registration_token_service.issue_token(
		email="expired@example.com",
		now_epoch=int(time.time()) - (24 * 60 * 60) - 5,
	)
	expired = client.post(
		"/api/auth/register-confirm",
		json={"token": expired_token, "password": "valid-passphrase-123"},
	)
	assert expired.status_code == 400
	assert expired.json()["error"]["message"] == "invalid or expired registration token"

	reusable_token = app.state.registration_token_service.issue_token(email="single-use@example.com")
	first = client.post(
		"/api/auth/register-confirm",
		json={"token": reusable_token, "password": "valid-passphrase-123"},
	)
	assert first.status_code == 200

	second = client.post(
		"/api/auth/register-confirm",
		json={"token": reusable_token, "password": "valid-passphrase-123"},
	)
	assert second.status_code == 400
	assert second.json()["error"]["message"] == "registration token already consumed"


def test_feature58_tenant_slug_collision_suffix_allocator(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	token_one = app.state.registration_token_service.issue_token(email="jerryschen@gmail.com")
	token_two = app.state.registration_token_service.issue_token(email="jerryschen@yahoo.com")
	token_three = app.state.registration_token_service.issue_token(email="jerryschen@outlook.com")

	first = client.post(
		"/api/auth/register-confirm",
		json={"token": token_one, "password": "valid-passphrase-123"},
	)
	second = client.post(
		"/api/auth/register-confirm",
		json={"token": token_two, "password": "valid-passphrase-123"},
	)
	third = client.post(
		"/api/auth/register-confirm",
		json={"token": token_three, "password": "valid-passphrase-123"},
	)

	assert first.status_code == 200
	assert second.status_code == 200
	assert third.status_code == 200

	assert first.json()["tenant_slug"] == "jerryschen"
	assert second.json()["tenant_slug"] == "jerryschen-1"
	assert third.json()["tenant_slug"] == "jerryschen-2"


def test_feature58_registration_suite(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	# Request verification link using duplicate-safe endpoint contract.
	request_response = client.post("/api/auth/register-request", json={"email": "suite-user@example.com"})
	assert request_response.status_code == 200
	assert request_response.json()["message"] == "If this email is valid, you'll receive a verification link"

	assert app.state.email_log_sink
	verification_link = app.state.email_log_sink[-1]["verification_link"]
	token = verification_link.split("token=", 1)[1]

	# Confirm registration and establish session.
	confirm_response = client.post(
		"/api/auth/register-confirm",
		json={"token": token, "password": "suite-passphrase-123"},
	)
	assert confirm_response.status_code == 200
	assert confirm_response.json()["redirect_to"] == "/registry"

	# Session cookie should permit auth-me access in the same client.
	auth_me = client.get("/api/auth/me")
	assert auth_me.status_code == 200
	auth_payload = auth_me.json()
	assert auth_payload["username"] == "suite-user@example.com"
	assert auth_payload["tenant_slug"] == "suite-user"


def test_feature59_password_reset_request_generic_response(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	known_email = "reset-known@example.com"
	app.state.user_store.create_user(
		username=known_email,
		plaintext_password="known-passphrase-123",
		role="user",
	)

	known_response = client.post("/api/auth/password-reset-request", json={"email": known_email})
	unknown_response = client.post("/api/auth/password-reset-request", json={"email": "reset-unknown@example.com"})

	assert known_response.status_code == 200
	assert unknown_response.status_code == 200

	expected_message = "If an account exists with that email, you'll receive a reset link"
	assert known_response.json() == {"message": expected_message}
	assert unknown_response.json() == {"message": expected_message}

	matching_events = [
		event for event in app.state.email_log_sink if event.get("email") == known_email and "reset_link" in event
	]
	assert len(matching_events) == 1
	assert matching_events[0]["reset_link"].startswith("http://localhost:3000/forgot-password/reset?token=")


def test_feature59_password_reset_request_rate_limit(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	for _ in range(5):
		response = client.post("/api/auth/password-reset-request", json={"email": "limit@example.com"})
		assert response.status_code in {200, 429}

	blocked = client.post("/api/auth/password-reset-request", json={"email": "limit@example.com"})
	assert blocked.status_code == 429
	blocked_body = blocked.json()
	assert blocked_body["error"]["code"] == "too_many_requests"
	assert blocked_body["error"]["message"] == "429 too many requests"
	assert blocked_body["error"]["request_id"]


def test_feature59_password_reset_confirm_success_invalidates_sessions(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	user = app.state.user_store.create_user(
		username="feature59-reset@example.com",
		plaintext_password="old-passphrase-123",
		role="user",
	)

	first_session, first_cookie = app.state.session_service.create_session(user_id=user.id)
	second_session, second_cookie = app.state.session_service.create_session(user_id=user.id)

	reset_token = app.state.password_reset_token_service.issue_token(email=user.username)
	response = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": reset_token, "new_password": "new-passphrase-123"},
	)

	assert response.status_code == 200
	payload = response.json()
	assert payload["message"] == "Password reset successful"
	assert payload["redirect_to"] == "/login"

	updated_user = app.state.user_store.get_by_username(user.username)
	assert updated_user is not None
	assert updated_user.verify_password("new-passphrase-123")
	assert not updated_user.verify_password("old-passphrase-123")

	with pytest.raises(PermissionError):
		app.state.session_service.validate_session_cookie(cookie_value=first_cookie.value)
	with pytest.raises(PermissionError):
		app.state.session_service.validate_session_cookie(cookie_value=second_cookie.value)

	assert first_session.session_id != second_session.session_id


def test_feature59_password_reset_confirm_invalid_token(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient
	import time

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	user = app.state.user_store.create_user(
		username="feature59-reset-invalid@example.com",
		plaintext_password="old-passphrase-123",
		role="user",
	)

	expired_token = app.state.password_reset_token_service.issue_token(
		email=user.username,
		now_epoch=int(time.time()) - (60 * 60) - 5,
	)
	expired_response = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": expired_token, "new_password": "new-passphrase-123"},
	)
	assert expired_response.status_code == 400
	assert expired_response.json()["error"]["message"] == "invalid or expired password reset token"

	malformed_response = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": "malformed-token", "new_password": "new-passphrase-123"},
	)
	assert malformed_response.status_code == 400
	assert malformed_response.json()["error"]["message"] == "invalid or expired password reset token"

	valid_token = app.state.password_reset_token_service.issue_token(email=user.username)
	first_response = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": valid_token, "new_password": "new-passphrase-123"},
	)
	assert first_response.status_code == 200

	second_response = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": valid_token, "new_password": "new-passphrase-123"},
	)
	assert second_response.status_code == 400
	assert second_response.json()["error"]["message"] == "password reset token already consumed"

	unchanged_user = app.state.user_store.get_by_username(user.username)
	assert unchanged_user is not None
	assert unchanged_user.verify_password("new-passphrase-123")


def test_feature59_password_policy_rejects_compromised_or_similar(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	register_token = app.state.registration_token_service.issue_token(email="policy-user@example.com")
	register_response = client.post(
		"/api/auth/register-confirm",
		json={"token": register_token, "password": "password123"},
	)
	assert register_response.status_code == 400
	assert register_response.json()["error"]["message"] == "password is too common"
	assert app.state.user_store.get_by_username("policy-user@example.com") is None

	user = app.state.user_store.create_user(
		username="similar-user@example.com",
		plaintext_password="original-passphrase-123",
		role="user",
	)
	before_hash = user.password_hash

	reset_token = app.state.password_reset_token_service.issue_token(email=user.username)
	reset_response = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": reset_token, "new_password": "similar-user-super-passphrase"},
	)
	assert reset_response.status_code == 400
	assert reset_response.json()["error"]["message"] == "password is too similar to account identifier"

	after_user = app.state.user_store.get_by_username(user.username)
	assert after_user is not None
	assert after_user.password_hash == before_hash


def test_feature59_password_reset_invalidates_all_relational_sessions(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	user = app.state.user_store.create_user(
		username="feature59-relational@example.com",
		plaintext_password="old-passphrase-123",
		role="user",
	)

	app.state.session_service.create_session(user_id=user.id)
	app.state.session_service.create_session(user_id=user.id)
	app.state.session_service.create_session(user_id=user.id)

	reset_token = app.state.password_reset_token_service.issue_token(email=user.username)
	confirm_response = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": reset_token, "new_password": "new-passphrase-123"},
	)
	assert confirm_response.status_code == 200

	sessions_root = tmp_path / "storage" / "auth" / "sessions"
	session_docs = []
	for path in sorted(sessions_root.glob("*.json")):
		session_docs.append(json.loads(path.read_text(encoding="utf-8")))

	user_sessions = [doc for doc in session_docs if doc.get("user_id") == user.id]
	assert len(user_sessions) == 3
	assert all(doc.get("invalidated_at_epoch") is not None for doc in user_sessions)


def test_feature59_forgot_password_suite(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	account_email = "feature59-suite@example.com"
	old_password = "suite-old-passphrase-123"
	new_password = "suite-new-passphrase-123"
	app.state.user_store.create_user(
		username=account_email,
		plaintext_password=old_password,
		role="user",
	)

	known_request = client.post("/api/auth/password-reset-request", json={"email": account_email})
	unknown_request = client.post("/api/auth/password-reset-request", json={"email": "unknown@example.com"})
	assert known_request.status_code == 200
	assert unknown_request.status_code == 200
	assert known_request.json() == unknown_request.json()

	reset_event = next(
		event for event in app.state.email_log_sink if event.get("email") == account_email and "reset_link" in event
	)
	reset_token = reset_event["reset_link"].split("token=", 1)[1]

	reset_confirm = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": reset_token, "new_password": new_password},
	)
	assert reset_confirm.status_code == 200
	assert reset_confirm.json()["redirect_to"] == "/login"

	old_login = client.post(
		"/api/auth/token",
		json={"username": account_email, "password": old_password, "tenant_slug": "feature59-suite"},
	)
	assert old_login.status_code == 401

	new_login = client.post(
		"/api/auth/token",
		json={"username": account_email, "password": new_password, "tenant_slug": "feature59-suite"},
	)
	assert new_login.status_code == 200
	assert new_login.json()["token_type"] == "Bearer"


def test_feature60_sqlite_auth_schema_and_indexes(tmp_path: Path) -> None:
	migration_path = (
		Path(__file__).resolve().parents[1]
		/ "server"
		/ "storage"
		/ "sql"
		/ "migrations"
		/ "001_auth_schema.sql"
	)
	migration_sql = migration_path.read_text(encoding="utf-8")

	db_path = tmp_path / "auth.db"
	connection = sqlite3.connect(db_path)
	try:
		connection.executescript(migration_sql)

		rows = connection.execute(
			"SELECT name FROM sqlite_master WHERE type='table'"
		).fetchall()
		tables = {row[0] for row in rows}
		for table_name in {"users", "tenants", "identities", "sessions", "one_time_tokens"}:
			assert table_name in tables

		# tenant_slug uniqueness
		connection.execute(
			"INSERT INTO tenants (tenant_slug, owner_user_id, visibility, created_at_epoch) VALUES (?, ?, ?, ?)",
			("tenant-alpha", "user-1", "private", 1),
		)
		with pytest.raises(sqlite3.IntegrityError):
			connection.execute(
				"INSERT INTO tenants (tenant_slug, owner_user_id, visibility, created_at_epoch) VALUES (?, ?, ?, ?)",
				("tenant-alpha", "user-2", "private", 1),
			)

		# identities(provider, provider_user_id) uniqueness
		connection.execute(
			"""
			INSERT INTO identities (
				user_id, provider, provider_user_id, provider_email, created_at_epoch, updated_at_epoch
			) VALUES (?, ?, ?, ?, ?, ?)
			""",
			("user-1", "local", "alice@example.com", "alice@example.com", 1, 1),
		)
		with pytest.raises(sqlite3.IntegrityError):
			connection.execute(
				"""
				INSERT INTO identities (
					user_id, provider, provider_user_id, provider_email, created_at_epoch, updated_at_epoch
				) VALUES (?, ?, ?, ?, ?, ?)
				""",
				("user-2", "local", "alice@example.com", "alice@example.com", 1, 1),
			)
	finally:
		connection.close()


def test_feature60_email_service_abstraction_dev_provider(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	known_email = "feature60-known@example.com"
	app.state.user_store.create_user(
		username=known_email,
		plaintext_password="known-passphrase-123",
		role="user",
	)

	register_response = client.post("/api/auth/register-request", json={"email": "feature60-new@example.com"})
	reset_response = client.post("/api/auth/password-reset-request", json={"email": known_email})

	assert register_response.status_code == 200
	assert reset_response.status_code == 200

	register_events = [
		event for event in app.state.email_log_sink if event.get("event_type") == "registration_verification"
	]
	reset_events = [event for event in app.state.email_log_sink if event.get("event_type") == "password_reset"]

	assert len(register_events) == 1
	assert len(reset_events) == 1
	assert register_events[0]["verification_link"].startswith("http://localhost:3000/signup/verify?token=")
	assert reset_events[0]["reset_link"].startswith("http://localhost:3000/forgot-password/reset?token=")


def test_feature60_env_secrets_and_single_use_tokens(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	register_secret = "feature60-register-secret"
	reset_secret = "feature60-reset-secret"
	frontend_url = "http://localhost:3099"
	monkeypatch.setenv("REGISTRY_REGISTER_TOKEN_SECRET", register_secret)
	monkeypatch.setenv("REGISTRY_PASSWORD_RESET_TOKEN_SECRET", reset_secret)
	monkeypatch.setenv("FRONTEND_URL", frontend_url)

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
		frontend_url=frontend_url,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	assert app.state.registration_token_service.signing_secret == register_secret
	assert app.state.password_reset_token_service.signing_secret == reset_secret

	register_email = "feature60-register@example.com"
	request_response = client.post("/api/auth/register-request", json={"email": register_email})
	assert request_response.status_code == 200

	register_event = next(
		event
		for event in app.state.email_log_sink
		if event.get("event_type") == "registration_verification" and event.get("email") == register_email
	)
	assert register_event["verification_link"].startswith(f"{frontend_url}/signup/verify?token=")
	register_token = register_event["verification_link"].split("token=", 1)[1]

	confirm_once = client.post(
		"/api/auth/register-confirm",
		json={"token": register_token, "password": "feature60-passphrase-123"},
	)
	assert confirm_once.status_code == 200

	confirm_twice = client.post(
		"/api/auth/register-confirm",
		json={"token": register_token, "password": "feature60-passphrase-123"},
	)
	assert confirm_twice.status_code == 400
	assert confirm_twice.json()["error"]["message"] == "registration token already consumed"

	reset_request = client.post("/api/auth/password-reset-request", json={"email": register_email})
	assert reset_request.status_code == 200

	reset_event = next(
		event for event in app.state.email_log_sink if event.get("event_type") == "password_reset"
	)
	assert reset_event["reset_link"].startswith(f"{frontend_url}/forgot-password/reset?token=")
	reset_token = reset_event["reset_link"].split("token=", 1)[1]

	reset_once = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": reset_token, "new_password": "feature60-new-passphrase-123"},
	)
	assert reset_once.status_code == 200

	reset_twice = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": reset_token, "new_password": "feature60-new-passphrase-123"},
	)
	assert reset_twice.status_code == 400
	assert reset_twice.json()["error"]["message"] == "password reset token already consumed"


def test_feature60_rehash_on_login_for_legacy_hash(tmp_path: Path) -> None:
	from dataclasses import replace
	import hashlib
	import re
	import secrets

	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	plaintext_password = "legacy-passphrase-123"
	user = app.state.user_store.create_user(
		username="feature60-legacy@example.com",
		plaintext_password=plaintext_password,
		role="user",
	)

	# Force a legacy scrypt hash so successful login should upgrade to Argon2id when available.
	legacy_salt = secrets.token_bytes(16)
	legacy_digest = hashlib.scrypt(plaintext_password.encode("utf-8"), salt=legacy_salt, n=2**14, r=8, p=1)
	legacy_hash = f"scrypt${legacy_salt.hex()}${legacy_digest.hex()}"
	app.state.user_store.save(replace(user, password_hash=legacy_hash))

	login_page = client.get("/login")
	assert login_page.status_code == 200
	match = re.search(r'name="csrf_token"\s+value="([^"]+)"', login_page.text)
	assert match is not None
	csrf_token = match.group(1)

	login_response = client.post(
		"/login",
		data={
			"username": user.username,
			"password": plaintext_password,
			"csrf_token": csrf_token,
		},
		follow_redirects=False,
	)
	assert login_response.status_code == 303

	updated_user = app.state.user_store.get_by_username(user.username)
	assert updated_user is not None
	assert updated_user.password_hash != legacy_hash
	assert updated_user.password_hash.startswith("$argon2") or updated_user.password_hash.startswith("scrypt$")


def test_feature60_subphase5_full_suite(tmp_path: Path) -> None:
	from fastapi.testclient import TestClient

	from server.app import create_app
	from server.config import ServerConfig

	config = ServerConfig(
		storage_backend="local",
		local_storage_root=tmp_path / "storage",
		s3_bucket="kinnoo-registry-dev",
		s3_region="us-east-1",
		s3_endpoint_url=None,
		s3_access_key_id=None,
		s3_secret_access_key=None,
		presign_ttl_seconds=120,
		max_upload_mb=5,
	)
	app = create_app(config=config)
	client = TestClient(app, base_url="https://testserver")

	# Baseline auth check should remain secure.
	auth_missing = client.get("/api/auth/me")
	assert auth_missing.status_code == 401

	# Registration request + confirm flow should still work end-to-end.
	register_email = "feature60-suite@example.com"
	request_response = client.post("/api/auth/register-request", json={"email": register_email})
	assert request_response.status_code == 200

	verification_event = next(
		event
		for event in app.state.email_log_sink
		if event.get("event_type") == "registration_verification" and event.get("email") == register_email
	)
	verification_token = verification_event["verification_link"].split("token=", 1)[1]
	confirm_response = client.post(
		"/api/auth/register-confirm",
		json={"token": verification_token, "password": "strong-passphrase-alpha-123"},
	)
	assert confirm_response.status_code == 200

	# Reset request + confirm must rotate credentials and keep login path working.
	reset_request = client.post("/api/auth/password-reset-request", json={"email": register_email})
	assert reset_request.status_code == 200
	reset_event = next(
		event
		for event in app.state.email_log_sink
		if event.get("event_type") == "password_reset" and event.get("email") == register_email
	)
	reset_token = reset_event["reset_link"].split("token=", 1)[1]
	reset_confirm = client.post(
		"/api/auth/password-reset-confirm",
		json={"token": reset_token, "new_password": "strong-passphrase-beta-456"},
	)
	assert reset_confirm.status_code == 200

	old_login = client.post(
		"/api/auth/token",
		json={"username": register_email, "password": "strong-passphrase-alpha-123", "tenant_slug": "feature60-suite"},
	)
	assert old_login.status_code == 401

	new_login = client.post(
		"/api/auth/token",
		json={
			"username": register_email,
			"password": "strong-passphrase-beta-456",
			"tenant_slug": "feature60-suite",
		},
	)
	assert new_login.status_code == 200


def test_feature60_sso_deferred_but_identity_schema_ready() -> None:
	schema_path = Path(__file__).resolve().parents[1] / "server" / "storage" / "sql" / "schema_auth.sql"
	planning_path = Path(__file__).resolve().parents[1] / "notes" / "phases" / "phase5-planning.md"
	tasks_path = Path(__file__).resolve().parents[1] / "TASKS.txt"

	schema_text = schema_path.read_text(encoding="utf-8")
	planning_text = planning_path.read_text(encoding="utf-8")
	tasks_text = tasks_path.read_text(encoding="utf-8")

	assert "UNIQUE(provider, provider_user_id)" in schema_text
	assert "Tenant ownership is based on internal `user_id`" in planning_text
	assert "Google/GitHub SSO implementation is explicitly deferred" in planning_text

	# Sub-phase 5 task block should not require provider-specific SSO endpoint implementation.
	subphase5_block = tasks_text[tasks_text.find("- id: task327") : tasks_text.find("- id: task331")]
	assert "google sso" not in subphase5_block.lower()
	assert "github sso" not in subphase5_block.lower()
