from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_feature94_group1() -> None:
    doc_path = ROOT / "docs" / "security-model.md"
    assert doc_path.exists()

    text = doc_path.read_text(encoding="utf-8")

    assert "# Security Model" in text
    assert "## Threat Model" in text
    assert "## Signing Model (Ed25519)" in text
    assert "## Integrity Verification" in text

    # AC2: threats + mitigations coverage
    assert "Main threats" in text
    assert "Current mitigations" in text


def test_feature94_group2() -> None:
    doc_path = ROOT / "docs" / "security-model.md"
    readme_path = ROOT / "README.md"

    text = doc_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")

    # AC4: auth flow sections
    assert "## Authentication and Session Security" in text
    assert "## Auth Flow Summary" in text
    assert "Registration" in text
    assert "Login" in text
    assert "JWT issuance" in text
    assert "Token refresh" in text
    assert "Logout" in text

    # AC5: README cross-reference
    assert "docs/security-model.md" in readme_text