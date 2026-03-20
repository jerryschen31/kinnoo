from __future__ import annotations

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.routes.publish import publish_archive


def _archive(name: str, version: str, visibility: str) -> tuple[str, bytes]:
    payload = (
        f"name: {name}\n"
        f"version: {version}\n"
        f"visibility: {visibility}\n"
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

    forbidden = client.get(
        "/api/agents/tenant-beta/agent-beta-private",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert forbidden.status_code == 403

    missing = client.get(
        "/api/agents/tenant-alpha/does-not-exist",
        headers={"Authorization": f"Bearer {alpha_reader_token}"},
    )
    assert missing.status_code == 404

    missing_auth = client.get("/api/agents")
    assert missing_auth.status_code == 401
