from __future__ import annotations

import re

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.routes.publish import publish_archive


def _extract_hidden_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def _archive(name: str, version: str, visibility: str, description: str, author: str) -> tuple[str, bytes]:
    payload = (
        f"name: {name}\n"
        f"version: {version}\n"
        f"visibility: {visibility}\n"
        f"description: {description}\n"
        f"author: {author}\n"
    ).encode("utf-8")

    from io import BytesIO
    import zipfile

    buff = BytesIO()
    with zipfile.ZipFile(buff, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("kinnoo.yaml", payload)
        archive.writestr("README.md", "web agents test")
    return f"{name}.kno", buff.getvalue()


def _login(client: TestClient, username: str, password: str) -> None:
    login_page = client.get("/login")
    assert login_page.status_code == 200
    csrf_token = _extract_hidden_csrf_token(login_page.text)

    login = client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert login.status_code == 303
    assert login.headers["location"] == "/agents"


def test_listing_and_search(tmp_path):
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

    app.state.user_store.create_user(
        username="admin",
        plaintext_password="admin-secret",
        role="admin",
    )

    publisher_token = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )

    published_agents = [
        ("alpha-writer", "1.0.0", "public", "writes docs", "alice"),
        ("alpha-search-tool", "1.1.0", "public", "keyword matching", "bob"),
    ]
    for name, version, visibility, description, author in published_agents:
        filename, archive_bytes = _archive(
            name=name,
            version=version,
            visibility=visibility,
            description=description,
            author=author,
        )
        result = publish_archive(
            authorization_header=f"Bearer {publisher_token}",
            filename=filename,
            archive_bytes=archive_bytes,
            token_service=app.state.token_service,
            storage_backend=app.state.storage_backend,
            metadata_manager=app.state.metadata_manager,
            max_upload_mb=app.state.config.max_upload_mb,
        )
        assert result.status_code == 201

    unauth_client = TestClient(app, base_url="https://testserver")
    redirect_response = unauth_client.get("/agents", follow_redirects=False)
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "/login"

    client = TestClient(app, base_url="https://testserver")
    _login(client, username="admin", password="admin-secret")

    listing = client.get("/agents?page=1&per_page=1")
    assert listing.status_code == 200
    assert "Published Agents" in listing.text
    assert "alpha-search-tool" in listing.text or "alpha-writer" in listing.text
    assert "Previous" in listing.text
    assert "Next" in listing.text
    assert "tenant-alpha" in listing.text

    second_page = client.get("/agents?page=2&per_page=1")
    assert second_page.status_code == 200
    assert "Page 2" in second_page.text

    search = client.get("/search?q=keyword")
    assert search.status_code == 200
    assert 'Results for "keyword": 1' in search.text
    assert "alpha-search-tool" in search.text
    assert "keyword matching" in search.text

    no_match = client.get("/search?q=not-found")
    assert no_match.status_code == 200
    assert "No matching agents found." in no_match.text


def test_profile_and_download(tmp_path):
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

    app.state.user_store.create_user(
        username="admin",
        plaintext_password="admin-secret",
        role="admin",
    )

    publisher_token = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )

    versions = [
        ("1.0.0", "first release", "alice"),
        ("1.1.0", "second release", "alice"),
    ]
    for version, description, author in versions:
        filename, archive_bytes = _archive(
            name="alpha-profile-agent",
            version=version,
            visibility="public",
            description=description,
            author=author,
        )
        result = publish_archive(
            authorization_header=f"Bearer {publisher_token}",
            filename=filename,
            archive_bytes=archive_bytes,
            token_service=app.state.token_service,
            storage_backend=app.state.storage_backend,
            metadata_manager=app.state.metadata_manager,
            max_upload_mb=app.state.config.max_upload_mb,
        )
        assert result.status_code == 201

    client = TestClient(app, base_url="https://testserver")
    _login(client, username="admin", password="admin-secret")

    profile = client.get("/agents/tenant-alpha/alpha-profile-agent")
    assert profile.status_code == 200
    assert "Agent Profile" in profile.text
    assert "alpha-profile-agent" in profile.text
    assert "1.0.0" in profile.text
    assert "1.1.0" in profile.text
    assert "Download" in profile.text

    download = client.get(
        "/agents/tenant-alpha/alpha-profile-agent/1.1.0/download",
        follow_redirects=False,
    )
    assert download.status_code == 303
    assert "location" in download.headers
    assert download.headers["location"].startswith("file://")

    missing = client.get("/agents/tenant-alpha/does-not-exist")
    assert missing.status_code == 404
