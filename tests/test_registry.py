from pathlib import Path
import importlib.util
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
