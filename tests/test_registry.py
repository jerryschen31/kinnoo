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
