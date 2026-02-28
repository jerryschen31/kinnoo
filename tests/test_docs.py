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