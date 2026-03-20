from __future__ import annotations

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig


def test_base_layout(tmp_path):
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
    templates = app.state.templates
    rendered = templates.get_template("base.html").render()

    assert "<header" in rendered
    assert "<nav" in rendered
    assert 'id="content"' in rendered
    assert "<footer" in rendered

    client = TestClient(app)
    css_response = client.get("/static/style.css")
    assert css_response.status_code == 200
    assert "text/css" in css_response.headers.get("content-type", "")
    assert ".site-header" in css_response.text
