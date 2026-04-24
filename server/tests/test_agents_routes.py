from __future__ import annotations

from dataclasses import replace
from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.routes.publish import publish_archive


def _archive(name: str, version: str, visibility: str) -> tuple[str, bytes]:
    payload = (
        f"name: {name}\n"
        f"version: {version}\n"
        f"visibility: {visibility}\n"
        "description: route metadata description\n"
        "author: route metadata author\n"
    ).encode("utf-8")

    from io import BytesIO
    import zipfile

    buff = BytesIO()
    with zipfile.ZipFile(buff, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("kinnoo.yaml", payload)
        archive.writestr("README.md", "metadata")
    return f"{name}.kno", buff.getvalue()


def test_list_and_detail(tmp_path):
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
    client = TestClient(app)

    alpha_reader_token = app.state.token_service.issue_token(
        subject="reader-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read"],
    )
    alpha_publisher_token = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )
    beta_publisher_token = app.state.token_service.issue_token(
        subject="publisher-beta",
        tenant_slug="tenant-beta",
        scopes=["registry:read", "registry:publish"],
    )

    for name, version in (("agent-alpha-a", "1.0.0"), ("agent-alpha-b", "1.0.0")):
        filename, archive_bytes = _archive(name=name, version=version, visibility="private")
        result = publish_archive(
            authorization_header=f"Bearer {alpha_publisher_token}",
            filename=filename,
            archive_bytes=archive_bytes,
            token_service=app.state.token_service,
            storage_backend=app.state.storage_backend,
            metadata_manager=app.state.metadata_manager,
            max_upload_mb=app.state.config.max_upload_mb,
        )
        assert result.status_code == 201

    beta_filename, beta_archive = _archive(
        name="agent-beta-private",
        version="2.0.0",
        visibility="private",
    )
    beta_result = publish_archive(
        authorization_header=f"Bearer {beta_publisher_token}",
        filename=beta_filename,
        archive_bytes=beta_archive,
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert beta_result.status_code == 201

    list_response = client.get(
        "/api/agents",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["total"] == 2
    listed_names = [item["agent_slug"] for item in list_body["items"]]
    assert listed_names == ["agent-alpha-a", "agent-alpha-b"]
    for item in list_body["items"]:
        assert item["name"] == item["agent_slug"]
        assert item["description"] == "route metadata description"
        assert item["author"] == "route metadata author"
        assert item["archive_size_bytes"] > 0

    paged_response = client.get(
        "/api/agents?offset=1&limit=1",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert paged_response.status_code == 200
    paged_body = paged_response.json()
    assert paged_body["total"] == 2
    assert len(paged_body["items"]) == 1
    assert paged_body["items"][0]["agent_slug"] == "agent-alpha-b"

    tenant_filtered = client.get(
        "/api/agents?tenant=tenant-alpha",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert tenant_filtered.status_code == 200
    assert tenant_filtered.json()["total"] == 2

    detail_response = client.get(
        "/api/agents/tenant-alpha/agent-alpha-a",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["tenant_slug"] == "tenant-alpha"
    assert detail_body["agent_slug"] == "agent-alpha-a"
    assert tuple(version["version"] for version in detail_body["versions"]) == ("1.0.0",)
    assert detail_body["latest_version"] == "1.0.0"
    assert detail_body["agent_manifest"]["name"] == "agent-alpha-a"

    forbidden = client.get(
        "/api/agents/tenant-beta/agent-beta-private",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert forbidden.status_code == 403
    forbidden_body = forbidden.json()
    assert forbidden_body["error"]["code"] == "forbidden"
    assert forbidden_body["error"]["message"]
    assert forbidden_body["error"]["request_id"]

    missing = client.get(
        "/api/agents/tenant-alpha/does-not-exist",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert missing.status_code == 404
    missing_body = missing.json()
    assert missing_body["error"]["code"] == "not_found"
    assert missing_body["error"]["message"]
    assert missing_body["error"]["request_id"]

    missing_auth = client.get("/api/agents")
    assert missing_auth.status_code == 401
    missing_auth_body = missing_auth.json()
    assert missing_auth_body["error"]["code"] == "unauthorized"
    assert missing_auth_body["error"]["message"]
    assert missing_auth_body["error"]["request_id"]


def test_security_report_falls_back_to_lambda_report_json(tmp_path):
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
    client = TestClient(app)

    token = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )

    filename, archive_bytes = _archive(name="agent-sec", version="1.0.0", visibility="private")
    result = publish_archive(
        authorization_header=f"Bearer {token}",
        filename=filename,
        archive_bytes=archive_bytes,
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert result.status_code == 201

    metadata = app.state.metadata_manager.get_version_metadata(
        tenant_slug="tenant-alpha",
        agent_slug="agent-sec",
        version="1.0.0",
    )
    assert metadata is not None
    app.state.metadata_manager.upsert_version_metadata(
        replace(
            metadata,
            security_status="",
            security_report=None,
        )
    )

    app.state.storage_backend.put_object(
        key="security-check/tenants/tenant-alpha/agents/agent-sec/versions/1.0.0/report.json",
        data=(
            '{"report":{"security_status":{"signature":"unsigned","archive":"pass","per_file":"pass"},'
            '"checks":[{"check_name":"signature","status":"unsigned","detail":"missing"}]}}\n'
        ).encode("utf-8"),
        content_type="application/json",
    )

    response = client.get(
        "/api/agents/tenant-alpha/agent-sec/1.0.0/security-report",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["security_status"]["signature"] == "unsigned"
    assert payload["checks"][0]["status"] == "unsigned"


def test_list_agents_show_only_mine_filters_out_other_tenant_public_agents(tmp_path):
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
    client = TestClient(app)

    alpha_reader_token = app.state.token_service.issue_token(
        subject="reader-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read"],
    )
    alpha_publisher_token = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )
    beta_publisher_token = app.state.token_service.issue_token(
        subject="publisher-beta",
        tenant_slug="tenant-beta",
        scopes=["registry:read", "registry:publish"],
    )

    alpha_filename, alpha_archive = _archive(
        name="agent-alpha-public",
        version="1.0.0",
        visibility="public",
    )
    alpha_result = publish_archive(
        authorization_header=f"Bearer {alpha_publisher_token}",
        filename=alpha_filename,
        archive_bytes=alpha_archive,
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert alpha_result.status_code == 201

    beta_filename, beta_archive = _archive(
        name="agent-beta-public",
        version="1.0.0",
        visibility="public",
    )
    beta_result = publish_archive(
        authorization_header=f"Bearer {beta_publisher_token}",
        filename=beta_filename,
        archive_bytes=beta_archive,
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert beta_result.status_code == 201

    all_visible = client.get(
        "/api/agents",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert all_visible.status_code == 200
    all_names = {item["agent_slug"] for item in all_visible.json()["items"]}
    assert all_names == {"agent-alpha-public", "agent-beta-public"}

    mine_only = client.get(
        "/api/agents?show_only_mine=true",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert mine_only.status_code == 200
    mine_payload = mine_only.json()
    assert mine_payload["total"] == 1
    assert mine_payload["items"][0]["tenant_slug"] == "tenant-alpha"
    assert mine_payload["items"][0]["agent_slug"] == "agent-alpha-public"


def test_list_agents_session_auth_defaults_to_mine_only(tmp_path):
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
    client = TestClient(app)

    footheman_user = app.state.user_store.create_user(
        username="footheman@example.com",
        plaintext_password="test-pass-123",
        role="user",
    )
    session_record, session_cookie = app.state.session_service.create_session(user_id=footheman_user.id)
    assert session_record.user_id == footheman_user.id

    footheman_publish_token = app.state.token_service.issue_token(
        subject="publisher-foo",
        tenant_slug="footheman",
        scopes=["registry:read", "registry:publish"],
    )
    jerryschen_publish_token = app.state.token_service.issue_token(
        subject="publisher-jerry",
        tenant_slug="jerryschen",
        scopes=["registry:read", "registry:publish"],
    )

    foo_filename, foo_archive = _archive(
        name="footheman-public-agent",
        version="1.0.0",
        visibility="public",
    )
    foo_result = publish_archive(
        authorization_header=f"Bearer {footheman_publish_token}",
        filename=foo_filename,
        archive_bytes=foo_archive,
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert foo_result.status_code == 201

    jerry_filename, jerry_archive = _archive(
        name="jerryschen-public-agent",
        version="1.0.0",
        visibility="public",
    )
    jerry_result = publish_archive(
        authorization_header=f"Bearer {jerryschen_publish_token}",
        filename=jerry_filename,
        archive_bytes=jerry_archive,
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert jerry_result.status_code == 201

    client.cookies.set(session_cookie.name, session_cookie.value)
    response = client.get("/api/agents")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["tenant_slug"] == "footheman"
    assert payload["items"][0]["agent_slug"] == "footheman-public-agent"
