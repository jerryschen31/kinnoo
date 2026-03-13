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


# [agent] test deprecated: Feature12 docs wording test is superseded by feature13 docs tests.
# def test_feature12_docs_cover_local_registry_flows() -> None:
#     ...


def test_feature13_docs_cover_archive_registry_refactor() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"

    assert "~/.kinnoo/archive/<agent>/<version>/<agent>.kno" in combined_text
    assert "KINNOO_ARCHIVE_ROOT" in combined_text

    assert "kinnoo publish <agent-name>" in combined_text
    assert "~/kinnoo-mock-registry-scratch/jerry/<agent>/<version>/<agent>.kno" in combined_text
    assert "untagged-<n>" in combined_text

    assert "kinnoo list" in combined_text
    assert "kinnoo list --local" in combined_text
    assert "kinnoo list --remote" in combined_text

    assert "kinnoo search <query>" in combined_text
    assert "kinnoo search --local <query>" in combined_text
    assert "kinnoo search --remote <query>" in combined_text

    assert "kinnoo install <name>" in combined_text
    assert "kinnoo install <name>==<version>" in combined_text
    assert "kinnoo install <file-path/file.kno>" in combined_text

    assert "kinnoo publish <archive.kno>" in combined_text
    assert "Migration" in combined_text or "migration" in combined_text


def test_feature14_docs_cover_preflight_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "kinnoo run <agent-dir> --preflight" in combined_text
    assert "kinnoo run ./my-agent --preflight" in combined_text

    assert "checklist" in combined_lower
    assert "runtime version" in combined_lower
    assert "env vars" in combined_lower
    assert "entrypoint" in combined_lower
    assert "dependencies" in combined_lower

    assert "Ready to run" in combined_text
    assert "Not ready to run" in combined_text
    assert "Remediation summary" in combined_text

    assert "without executing" in combined_lower
    assert "does not execute agent entrypoint logic" in combined_lower

    assert "names-only" in combined_lower or "names only" in combined_lower
    assert "never prints env var values" in combined_lower


def test_feature15_docs_cover_trust_baseline() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "Continue with install? [y/N]:" in combined_text
    assert "--yes" in combined_text or "-y" in combined_text

    assert "This agent is from an unverified source." in combined_text
    assert "This agent is from an unverified source. Continue? (y/n):" in combined_text
    assert ".sha256" in combined_text

    assert "~/.kinnoo/logs/run.<TIMESTAMP>.log" in combined_text
    assert "utc" in combined_lower
    assert "timestamp" in combined_text
    assert "agent_name" in combined_text
    assert "agent-version" in combined_text
    assert "runtime_type" in combined_text
    assert "exit_code" in combined_text
    assert "never includes input text" in combined_lower or "never include input text" in combined_lower

    assert "Security sweep:" in combined_text
    assert "Security sweep: no env var exposure patterns detected (heuristic)" in combined_text
    assert "heuristic scan — may produce false positives; not a substitute for code review" in combined_lower

    assert "no env var or secret values" in combined_lower
    assert "names-only" in combined_lower or "names only" in combined_lower


def test_feature16_docs_cover_checksum_lifecycle() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "archive integrity" in combined_lower
    assert ".kno.sha256" in combined_text
    assert "<sha256>  <archive-filename>" in combined_text

    assert "[kinnoo pack] Checksum sidecar written: <path>" in combined_text

    assert "[kinnoo install] Archive checksum verified." in combined_text
    assert (
        "Archive integrity check failed — the file may be corrupted or tampered with"
        in combined_text
    )
    assert "No checksum file found — archive integrity not verified" in combined_text

    assert "- Checksum (SHA256): <digest>" in combined_text

    assert "Published checksum sidecar: <path>" in combined_text
    assert "Published checksum sidecar: (none found at source)" in combined_text


def test_feature17_docs_cover_pack_size_reporting() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "archive size" in combined_lower
    assert "[kinnoo pack] Archive size: <human-readable>" in combined_text

    assert (
        "Warning: archive is large (X MB). Consider whether all dependencies are necessary."
        in combined_text
    )

    assert "- Archive Size: <human-readable>" in combined_text

    assert "kinnoo list" in combined_text
    assert "kinnoo list --local" in combined_text
    assert "kinnoo list --remote" in combined_text
    assert "| size: <human-readable>" in combined_text

    assert "B" in combined_text
    assert "KB" in combined_text
    assert "MB" in combined_text
    assert "GB" in combined_text