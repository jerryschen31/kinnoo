from __future__ import annotations

from io import BytesIO
import zipfile

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.routes.publish import publish_archive


def _archive_bytes(*, name: str, version: str, visibility: str, description: str) -> bytes:
    payload = BytesIO()
    with zipfile.ZipFile(payload, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "kinnoo.yaml",
            (
                f"name: {name}\n"
                f"version: {version}\n"
                f"visibility: {visibility}\n"
                f"description: {description}\n"
            ),
        )
        archive.writestr("README.md", "search test")
    return payload.getvalue()


def _publish(
    *,
    app,
    token: str,
    name: str,
    version: str,
    visibility: str,
    description: str,
) -> None:
    result = publish_archive(
        authorization_header=f"Bearer {token}",
        filename=f"{name}.kno",
        archive_bytes=_archive_bytes(
            name=name,
            version=version,
            visibility=visibility,
            description=description,
        ),
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert result.status_code == 201


def test_search_endpoint(tmp_path):
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=300,
        max_upload_mb=5,
    )
    app = create_app(config=config)
    client = TestClient(app)

    alpha_publisher = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )
    beta_publisher = app.state.token_service.issue_token(
        subject="publisher-beta",
        tenant_slug="tenant-beta",
        scopes=["registry:read", "registry:publish"],
    )
    alpha_reader = app.state.token_service.issue_token(
        subject="reader-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read"],
    )

    _publish(
        app=app,
        token=alpha_publisher,
        name="alpha-writer",
        version="1.0.0",
        visibility="private",
        description="agent writes release notes",
    )
    _publish(
        app=app,
        token=alpha_publisher,
        name="alpha-analyzer",
        version="1.0.0",
        visibility="public",
        description="analysis keyword matching",
    )
    _publish(
        app=app,
        token=beta_publisher,
        name="beta-secret-tool",
        version="1.0.0",
        visibility="private",
        description="analysis hidden from alpha tenant",
    )

    by_name = client.get(
        "/api/search?q=writer",
        headers={"Authorization": f"Bearer {alpha_reader}"},
    )
    assert by_name.status_code == 200
    body_name = by_name.json()
    assert body_name["total"] == 1
    assert body_name["items"][0]["agent_slug"] == "alpha-writer"

    by_description = client.get(
        "/api/search?q=keyword",
        headers={"Authorization": f"Bearer {alpha_reader}"},
    )
    assert by_description.status_code == 200
    body_description = by_description.json()
    assert body_description["total"] == 1
    assert body_description["items"][0]["agent_slug"] == "alpha-analyzer"

    empty = client.get(
        "/api/search?q=does-not-exist",
        headers={"Authorization": f"Bearer {alpha_reader}"},
    )
    assert empty.status_code == 200
    assert empty.json()["total"] == 0

    paged = client.get(
        "/api/search?q=alpha&offset=1&limit=1",
        headers={"Authorization": f"Bearer {alpha_reader}"},
    )
    assert paged.status_code == 200
    body_paged = paged.json()
    assert body_paged["total"] == 2
    assert len(body_paged["items"]) == 1

    hidden = client.get(
        "/api/search?q=hidden",
        headers={"Authorization": f"Bearer {alpha_reader}"},
    )
    assert hidden.status_code == 200
    assert hidden.json()["total"] == 0

    missing_auth = client.get("/api/search?q=alpha")
    assert missing_auth.status_code == 401
    missing_auth_body = missing_auth.json()
    assert missing_auth_body["error"]["code"] == "unauthorized"
    assert missing_auth_body["error"]["message"]
    assert missing_auth_body["error"]["request_id"]

    empty_query = client.get(
        "/api/search?q=",
        headers={"Authorization": f"Bearer {alpha_reader}"},
    )
    assert empty_query.status_code == 400
    empty_query_body = empty_query.json()
    assert empty_query_body["error"]["code"] == "bad_request"
    assert empty_query_body["error"]["message"]
    assert empty_query_body["error"]["request_id"]


def test_search_show_only_mine_filters_public_cross_tenant_results(tmp_path):
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=300,
        max_upload_mb=5,
    )
    app = create_app(config=config)
    client = TestClient(app)

    alpha_publisher = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )
    beta_publisher = app.state.token_service.issue_token(
        subject="publisher-beta",
        tenant_slug="tenant-beta",
        scopes=["registry:read", "registry:publish"],
    )
    alpha_reader = app.state.token_service.issue_token(
        subject="reader-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read"],
    )

    _publish(
        app=app,
        token=alpha_publisher,
        name="alpha-shared-agent",
        version="1.0.0",
        visibility="public",
        description="shared utility",
    )
    _publish(
        app=app,
        token=beta_publisher,
        name="beta-shared-agent",
        version="1.0.0",
        visibility="public",
        description="shared utility",
    )

    all_visible = client.get(
        "/api/search?q=shared",
        headers={"Authorization": f"Bearer {alpha_reader}"},
    )
    assert all_visible.status_code == 200
    all_items = all_visible.json()["items"]
    assert {item["agent_slug"] for item in all_items} == {"alpha-shared-agent", "beta-shared-agent"}

    mine_only = client.get(
        "/api/search?q=shared&show_only_mine=true",
        headers={"Authorization": f"Bearer {alpha_reader}"},
    )
    assert mine_only.status_code == 200
    mine_payload = mine_only.json()
    assert mine_payload["total"] == 1
    assert mine_payload["items"][0]["tenant_slug"] == "tenant-alpha"
    assert mine_payload["items"][0]["agent_slug"] == "alpha-shared-agent"
