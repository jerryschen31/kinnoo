from pathlib import Path
import re
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kinnoo.validator import validate_manifest_data  # noqa: E402


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


def test_feature18_docs_cover_input_safety_guard() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "Input Safety Guard" in combined_text
    assert "--no-guard" in combined_text

    assert "SQL injection" in combined_text
    assert "shell" in combined_lower
    assert "path traversal" in combined_lower
    assert "SSRF" in combined_text
    assert "XSS" in combined_text
    assert "template injection" in combined_lower

    assert "Protocol" in combined_text
    assert "type-aware" in combined_lower
    assert "non-blocking" in combined_lower


def test_feature42_docs_cover_json_contract_guidance() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "JSON I/O Contract (Feature42)" in combined_text
    assert "--json-input" in combined_text
    assert "--json-file" in combined_text
    assert "outputs.type" in combined_text
    assert "stdout must be valid JSON" in combined_text

    assert "kinnoo inspect" in combined_text
    assert "Input Types" in combined_text
    assert "Output Types" in combined_text
    assert "JSON Contract" in combined_text

    assert "kinnoo run <agent-dir> --preflight" in combined_text
    assert "manifest I/O contract" in combined_text

    assert "text workflows remain" in combined_lower
    assert "unchanged" in combined_lower


def test_feature33_manifest_extension_docs_examples() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "runtime.package_manager" in combined_text
    assert "channels" in combined_text
    assert "skills" in combined_text
    assert "state_dirs" in combined_text
    assert "npm" in combined_text and "pnpm" in combined_text

    assert "framework: openclaw" in combined_text
    assert "openclaw-agent" in combined_text
    assert "type: daemon" in combined_text
    assert "language: nodejs" in combined_text
    assert "stdio" in combined_text

    assert "generic-node-agent" in combined_text
    assert "framework: custom-framework" in combined_text
    assert "type: one-shot" in combined_text

    assert "non-openclaw" in combined_lower


def test_feature35_docs_cover_mutable_state_semantics() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "Feature35 mutable state snapshots (`state_dirs`)" in combined_text
    assert "mutable runtime state" in combined_lower
    assert "distinct from immutable `assets`" in combined_text

    assert "state_snapshots/<state-dir>/..." in combined_text
    assert "state_snapshots/memory/core/profile.json" in combined_text
    assert "<install-target>/memory/core/profile.json" in combined_text

    assert "exclude" in combined_lower
    assert "daily/*.md" in combined_text
    assert "secrets/*" in combined_text

    assert "--state-overwrite" in combined_text
    assert "warning-first" in combined_lower
    assert "non-destructive" in combined_lower

    assert "without `state_dirs`" in combined_text
    assert "asset-only" in combined_lower


def test_feature35_docs_cover_mutable_state_semantics_and_assets_compatibility() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"
    readme_doc = repo_root / "README.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    readme_text = readme_doc.read_text(encoding="utf-8")
    combined_text = f"{schema_text}\n{readme_text}"
    combined_lower = combined_text.lower()

    assert "mutable state" in combined_lower
    assert "state_dirs" in combined_text
    assert "immutable assets" in combined_lower or "immutable `assets`" in combined_text
    assert "state_snapshots/" in combined_text

    assert "exclude" in combined_lower
    assert "daily/*.md" in combined_text
    assert "secrets/*" in combined_text
    assert "omitted" in combined_lower

    assert "--state-overwrite" in combined_text
    assert "warning-first" in combined_lower
    assert "non-destructive" in combined_lower

    assert "manifests without `state_dirs`" in combined_text or "without state_dirs" in combined_lower
    assert "asset-only behavior" in combined_lower or "assets" in combined_lower
    assert "remain valid" in combined_lower


def test_feature62_openclaw_schema_docs_consistency() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    schema_doc = repo_root / "docs" / "manifest-schema-reference.md"

    schema_text = schema_doc.read_text(encoding="utf-8")
    section_start = "### Feature62 openclaw-skill schema contract (`type`, `provenance`)"
    assert section_start in schema_text

    section_text = schema_text.split(section_start, 1)[1]
    next_section_index = section_text.find("\n### ")
    if next_section_index != -1:
        section_text = section_text[:next_section_index]

    assert "source_registry" in section_text
    assert "source_version" in section_text
    assert "source_slug" in section_text
    assert "source_url" in section_text
    assert "at least one" in section_text

    assert "channels`, `skills`, and `state_dirs`" in section_text
    assert "validation fails" in section_text
    assert "Remove `channels`, `skills`, and `state_dirs`" in section_text

    yaml_blocks = re.findall(r"```yaml\n(.*?)```", section_text, flags=re.DOTALL)
    assert len(yaml_blocks) >= 3, "Expected canonical Feature62 YAML examples in docs"

    for block in yaml_blocks:
        manifest_data = yaml.safe_load(block)
        assert isinstance(manifest_data, dict)
        is_valid, errors = validate_manifest_data(manifest_data)
        assert is_valid is True, (
            "Expected Feature62 docs YAML example to pass validation; "
            f"errors: {errors}; yaml block: {block}"
        )


def test_feature68_workflow_contract_and_envs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    workflow_path = repo_root / ".github" / "workflows" / "kinnoo-publish.yml"
    readme_path = repo_root / "README.md"
    schema_path = repo_root / "docs" / "manifest-schema-reference.md"

    assert workflow_path.exists(), "Expected Feature68 workflow file to exist"

    workflow_text = workflow_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")
    schema_text = schema_path.read_text(encoding="utf-8")
    combined_docs = f"{readme_text}\n{schema_text}"

    workflow_data = yaml.safe_load(workflow_text)
    assert isinstance(workflow_data, dict)

    jobs = workflow_data.get("jobs")
    assert isinstance(jobs, dict)
    publish_job = jobs.get("publish")
    assert isinstance(publish_job, dict)

    job_env = publish_job.get("env")
    assert isinstance(job_env, dict)
    assert "KINNOO_REGISTRY_URL" in job_env
    assert "KINNOO_REGISTRY_TOKEN" in job_env
    assert "KINNOO_TENANT_SLUG" in job_env
    assert "KINNOO_CI_STRICT_MODE" in job_env

    steps = publish_job.get("steps")
    assert isinstance(steps, list)
    step_names = [step.get("name", "") for step in steps if isinstance(step, dict)]
    assert any("Install" in str(name) for name in step_names)
    assert any("preflight" in str(name).lower() for name in step_names)
    assert any("Pack" in str(name) for name in step_names)
    assert any("Publish" in str(name) for name in step_names)

    assert "python3 src/kinnoo/cli.py check" in workflow_text
    assert "python3 src/kinnoo/cli.py pack" in workflow_text
    assert "python3 src/kinnoo/cli.py publish" in workflow_text
    assert "--remote" in workflow_text

    assert "KINNOO_REGISTRY_URL" in combined_docs
    assert "KINNOO_REGISTRY_TOKEN" in combined_docs
    assert "KINNOO_TENANT_SLUG" in combined_docs
    assert "KINNOO_CI_STRICT_MODE" in combined_docs


def test_feature68_ci_failure_and_troubleshooting_docs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    workflow_path = repo_root / ".github" / "workflows" / "kinnoo-publish.yml"
    readme_path = repo_root / "README.md"
    schema_path = repo_root / "docs" / "manifest-schema-reference.md"

    workflow_text = workflow_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")
    schema_text = schema_path.read_text(encoding="utf-8")
    combined_docs = f"{readme_text}\n{schema_text}"
    combined_lower = combined_docs.lower()

    assert "set -euo pipefail" in workflow_text
    assert "non-zero" in combined_lower
    assert "troubleshooting common ci failures" in combined_lower
    assert "signing failures" in combined_lower
    assert "publish failures" in combined_lower

    for required_secret in (
        "KINNOO_REGISTRY_URL",
        "KINNOO_REGISTRY_TOKEN",
        "KINNOO_TENANT_SLUG",
    ):
        assert required_secret in combined_docs

    expected_commands = (
        "python3 src/kinnoo/cli.py check",
        "python3 src/kinnoo/cli.py pack",
        "python3 src/kinnoo/cli.py publish",
    )
    for command in expected_commands:
        assert command in workflow_text

    assert "kinnoo publish --remote" in combined_docs


def test_feature70_landing_and_readme_phase6_messaging() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    landing_path = repo_root / "web" / "app" / "(public)" / "page.tsx"
    feature_grid_path = repo_root / "web" / "components" / "blocks" / "FeatureGrid.tsx"
    readme_path = repo_root / "README.md"

    landing_text = landing_path.read_text(encoding="utf-8")
    feature_grid_text = feature_grid_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")

    combined_landing = f"{landing_text}\n{feature_grid_text}".lower()
    readme_lower = readme_text.lower()

    assert "openclaw" in combined_landing
    assert "clawhub" in combined_landing
    assert "trust" in combined_landing
    assert "provenance" in combined_landing

    required_phase6_commands = (
        "kinnoo login",
        "kinnoo logout",
        "kinnoo import --source clawhub",
        "kinnoo sync clawhub",
        "kinnoo test",
        "kinnoo publish",
    )
    for command in required_phase6_commands:
        assert command in readme_lower

    assert "phase 6 command matrix" in readme_lower
    assert "clawhub mirror attribution model" in readme_lower