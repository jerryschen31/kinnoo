from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_feature101_group1() -> None:
    dockerfile = _read("Dockerfile")

    assert "FROM python:3.11-slim AS builder" in dockerfile
    assert "FROM python:3.11-slim AS runtime" in dockerfile
    assert "COPY --from=builder /install /usr/local" in dockerfile
    assert "useradd" in dockerfile
    assert "USER appuser" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "/health" in dockerfile


def test_feature101_group2() -> None:
    compose_file = Path("docker-compose.yml")
    assert compose_file.exists(), "docker-compose.yml must exist for feature101 group2"

    compose_text = compose_file.read_text(encoding="utf-8")
    assert "services:" in compose_text
    assert "server:" in compose_text
    assert "8000:8000" in compose_text


def test_feature101_group3_server_dependencies() -> None:
    server_requirements = _read("server/requirements.txt")
    assert "PyYAML" in server_requirements
