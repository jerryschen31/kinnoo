from pathlib import Path


def test_feature9_schema_docs_cover_optional_fields_and_constraints() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")

    assert "description" in schema_text
    assert "author" in schema_text
    assert "license" in schema_text
    assert "env_vars" in schema_text
    assert "list[string]" in schema_text
    assert "non-empty" in schema_text
    assert "V1 compatibility note" in schema_text
    assert "remain valid" in schema_text

    assert "Manifest optional metadata (Feature9)" in readme_text
    assert "env_vars" in readme_text
    assert "non-empty string" in readme_text


def test_feature10_docs_cover_env_vars_security_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")

    schema_lower = schema_text.lower()
    readme_lower = readme_text.lower()

    for text in (schema_lower, readme_lower):
        assert "process environment" in text
        assert "agent-local `.env`" in text
        assert "masked interactive prompt" in text or "masked prompt" in text
        assert "never be printed" in text
        assert "never" in text and "logged" in text
        assert "persisted" in text
        assert "variable names" in text

    assert "OPENAI_API_KEY" in schema_text
    assert "ANTHROPIC_API_KEY" in schema_text