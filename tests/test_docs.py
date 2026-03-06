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


def test_feature11_docs_cover_inspect_usage_and_missing_file_guidance() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"

    assert "kinnoo inspect" in combined_text
    assert "kinnoo inspect <agent-dir>" in combined_text
    assert "kinnoo inspect <archive.kno>" in combined_text
    assert "kinnoo inspect ./my-agent" in combined_text
    assert "kinnoo inspect ./my-agent.kno" in combined_text

    assert "human-readable" in combined_text
    assert "missing optional fields" in combined_text
    assert "env_vars" in combined_text
    assert "names-only" in combined_text or "names only" in combined_text

    assert "kinnoo.yaml" in combined_text
    assert "requirements.txt" in combined_text
    assert "pip install uv" in combined_text
    assert "uv export --format requirements-txt > requirements.txt" in combined_text

    assert "Usage: kinnoo inspect <target>" in combined_text
    assert "invalid zip-based `.kno`" in combined_text or "invalid zip-based .kno" in combined_text
    assert "Error: Manifest validation failed." in combined_text


    def test_feature12_docs_cover_local_registry_flows() -> None:
        root = Path(__file__).resolve().parents[1]
        readme = (root / "README.md").read_text(encoding="utf-8")
        schema = (root / "docs" / "manifest-schema-reference.md").read_text(encoding="utf-8")

        expected = [
            "kinnoo publish <archive.kno>",
            "kinnoo publish <archive.kno> --local",
            "~/.kinnoo/registry/<name>/<version>/",
            "kinnoo install <name>",
            "kinnoo install <name>==<version>",
            "kinnoo install <file.kno>",
            "kinnoo list",
            "kinnoo search <query>",
        ]
        for token in expected:
            assert token in readme
            assert token in schema

        assert "kinnoo install research-agent" in readme
        assert "kinnoo install research-agent==1.1.0" in readme
        assert "kinnoo install research-agent" in schema
        assert "kinnoo install research-agent==1.1.0" in schema