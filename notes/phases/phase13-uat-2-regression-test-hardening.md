# Phase 13 UAT-2: Regression Test Hardening

## Prompt 1 (Human)
> Suggest ways to make regression testing more robust and less prone to breaking. Consider if we need refactoring of code or test organization. Tests should discover TRUE BUGS, not drift.

## Response 1 (Agent)

### Diagnosis: Why 129 tests are failing

I categorized all 129 failures from the April 16 full-suite run into **six root-cause patterns**. Critically, **almost none of these are true bugs** — they are test-code fragility.

---

#### Pattern 1: CLI argument grammar drift (~40 tests, mostly `test_init.py`)

Tests hardcode exact CLI argument ordering:
```python
run_cli(["init", "chatgpt", "--minimal", agent_name], cwd=tmp_path)
```
The `init` subcommand's argparse schema changed (e.g., positional `agent_name` moved, `--framework` became a positional arg), so argparse now rejects the old invocation with `unrecognized arguments`. The *feature* still exists — the *calling convention* changed.

**This is the #1 source of ghost failures.**

#### Pattern 2: Exact-string assertions on CLI output (~15 tests, `test_cli.py`, `test_cli_registry_modes.py`)

Tests assert exact help text:
```python
assert "daemon agents:" in output
assert "{stop,attach,logs}" in output
assert "replacement=kinnoo run <agent-dir> '<prompt>' [--thinking <level>] [--json]" in output
```
Any cosmetic change — adding a subcommand, renaming a flag, reordering groups — breaks these. The actual behavior is fine; the *string representation* of the behavior changed.

#### Pattern 3: Validator schema tightening (~29 tests, `test_validator.py`)

The validator added `entrypoint path exists` checking. Old test fixtures write YAML manifests but don't create the actual `run.py` file on disk. So `validate()` now returns `["Declared entrypoint path not found: 'run.py'."]`. Not a bug — a stricter invariant that the fixtures don't satisfy.

#### Pattern 4: Regression gate meta-tests (~6 tests, `test_regression_v1.py`)

Tests like `test_feature21_framework_templates_do_not_regress_existing_frameworks` literally shell out to `pytest` to run *other* tests. If any inner test breaks (for any of the above reasons), the gate cascades. These tests amplify every other failure.

#### Pattern 5: Exact infrastructure string assertions (~3 tests, `test_feature_103.py`, `test_feature_106.py`)

Tests assert exact Terraform config strings like:
```python
assert 'bucket       = "kinnoo-terraform-state-dev"' in backend_tf
```
Backend config was refactored to use `-backend-config` HCL files, so the hardcoded string no longer appears. Not a bug — an intentional infrastructure improvement.

#### Pattern 6: Removed/deprecated CLI commands (~5 tests, `test_cli_registry_modes.py`)

Tests invoke commands like `sync` that were removed from the CLI. The tests should have been deprecated when the command was removed, but weren't.

---

### Recommendations

#### A. Test what the code *does*, not what it *says*

**Problem:** The majority of failures come from asserting exact strings (help text, error messages, deprecation warnings). These are the most volatile parts of a CLI — they change with every UX polish.

**Fix approach — Semantic assertions over literal assertions:**

| Instead of | Use |
|---|---|
| `assert "daemon agents:" in output` | `assert result.returncode == 0` (help renders without error) |
| `assert "{stop,attach,logs}" in output` | Assert each subcommand exists individually, or parse argparse's structured output |
| `assert "Usage: kinnoo install <archive-path>" in result.stderr` | `assert "usage:" in result.stderr.lower()` + `assert result.returncode != 0` |
| `assert first_line == "🍊 Run a kinnoo agent"` | `assert first_line.startswith("🍊")` and `assert "run" in first_line.lower()` |

**For help text specifically:** Create one dedicated "help text contract" test per subcommand that asserts the *structural* properties (required args are documented, deprecated flags are absent). Don't assert the exact rendered string — it will break every time you add a flag.

#### B. Decouple test fixtures from production validation

**Problem:** `test_validator.py` creates YAML-only manifests without the actual entrypoint file. When the validator got stricter, all those tests broke.

**Fix approach — Use a test-specific validation mode or complete fixtures:**

1. **Option 1 (preferred):** Have `validate()` accept an optional `check_paths=True` parameter. Test-only callers pass `check_paths=False` when testing schema logic. Production callers keep the default.
2. **Option 2:** Make the validator fixtures complete — always create the entrypoint file alongside the YAML. Add a `_write_complete_agent(data, tmp_path)` helper that writes both.
3. **Option 3:** Use `validate_manifest_data(data)` (which already exists) for schema-only tests, and reserve `validate(path)` for integration tests that test the full on-disk validation.

This is a modest refactor: you separate "is the schema valid?" (unit-testable with just a dict) from "is the on-disk agent valid?" (integration test requiring real files).

#### C. Stop writing regression gate meta-tests

**Problem:** `test_regression_v1.py` runs `subprocess.run(pytest, ...)` inside test functions. This creates an amplification layer where N inner failures produce N+M total failures. It also makes test output confusing — you see a gate failure and have to dig to find the actual root cause.

**Fix:** Delete `test_regression_v1.py` entirely. Use **pytest markers** instead:

```python
# In test_init.py
@pytest.mark.regression
@pytest.mark.feature21
def test_feature21_pydanticai_template_generation(tmp_path):
    ...
```

Then in CI:
```bash
python -m pytest -m "regression" --tb=short
```

This gives you the same "did we regress?" signal without the nesting. Failures are flat and directly traceable. You can define `conftest.py` markers for every feature and every phase.

#### D. Use CLI invocation helpers that abstract argument grammar

**Problem:** 40+ tests each hardcode the exact `sys.argv` to invoke `kinnoo init`. When the argparse schema changes, you update 40 tests.

**Fix — Create a test utility module `tests/helpers.py`:**

```python
def kinnoo_init(framework: str, agent_name: str, *, cwd: Path, language: str = "python", minimal: bool = False) -> tuple[int, str, str]:
    """Invoke kinnoo init with the current CLI contract."""
    args = ["init", framework]
    if language != "python":
        args += ["--language", language]
    if minimal:
        args += ["--minimal"]
    args.append(agent_name)
    return run_cli(args, cwd=cwd)
```

When the CLI grammar changes, you update **one function**. All 40 tests keep working (or break only if the *feature semantics* actually changed).

Similarly for `kinnoo_pack()`, `kinnoo_install()`, `kinnoo_run()`, etc.

#### E. Adopt a deprecation-on-removal workflow

**Problem:** When a CLI command (`sync`) or flag (`--framework`, `--thinking`) is removed, the tests that use it aren't deprecated at the same time.

**Fix — SWE agent workflow rule:**
> When a PR removes or renames a CLI command, flag, or public API, the same PR MUST mark all tests that reference the old surface as `@pytest.mark.skip(reason="deprecated: <command> removed in <feature>")` or update them to use the new surface. The manifest validator should check that no test references a deprecated feature surface.

This is a process fix, not a code fix. Add it to `swe.agent.md`.

#### F. Separate schema/unit tests from integration/CLI tests

**Problem:** `test_validator.py` mixes pure schema validation (dict in, bool out) with on-disk integration tests. `test_init.py` mixes template structure checks with CLI invocation tests.

**Fix — Test file organization principle:**

| Layer | What it tests | How it invokes | Breaks when... |
|---|---|---|---|
| **Unit** (`test_validator_schema.py`) | Manifest schema rules | `validate_manifest_data(dict)` | Schema rules change |
| **Integration** (`test_validator_integration.py`) | On-disk validation | `validate(path)` with real files | File-existence rules change |
| **CLI** (`test_cli_init.py`) | CLI arg parsing + dispatch | `subprocess.run(cli.py, ...)` | Argparse grammar changes |
| **E2E** (`test_e2e_init_pack_install.py`) | Full workflow | CLI subprocess chain | Workflow semantics change |

You don't need to move all tests today. But new tests should follow this layering. Over time, migrate the most fragile ones.

---

### On Code Refactoring

The code itself (`src/kinnoo/`) is not the primary problem — the tests are. But there are two modest code changes that will make tests much more stable:

1. **`validate()` ↔ `validate_manifest_data()` split** (already partially done): Make the pure-schema function (`validate_manifest_data`) the primary test target for schema tests. Keep `validate(path)` for integration testing. This requires no new code — just test migration.

2. **CLI `init` argument contract**: The `init` subcommand should have a stable, documented argument grammar. If `kinnoo init <framework> <agent-name>` is the contract, document it and test it as a contract. If you're going to change it, that's a breaking change and previous tests should be migrated in the same PR.

3. **Structured CLI output**: For any tests that need to verify *what* the CLI did (not how it displayed it), prefer `--json` output mode (which you've already built for `run`). This gives tests a stable machine-readable contract. JSON keys are much more stable than formatted text.

---

### Summary Table

| Fix | Effort | Impact | Tests Fixed |
|---|---|---|---|
| A. Semantic assertions | Medium | High | ~15 help-text tests |
| B. Validator fixture completeness | Low | High | ~29 validator tests |
| C. Delete meta-gate tests, use markers | Low | Medium | ~6 regression gates |
| D. CLI invocation helpers | Medium | Very High | ~40 init/CLI tests |
| E. Deprecation-on-removal workflow | Low (process) | Ongoing | Prevents future drift |
| F. Test layering | High (gradual) | Very High | Structural, long-term |

The highest-ROI immediate actions are **B** (fix validator fixtures — 29 tests for maybe 30 minutes of work) and **D** (CLI helpers — 40 tests broken by one argument grammar change).

---

Copy the above into `notes/phase13-uat-2-regression-test-hardening.md`. Here's the TL;DR:

**The 129 failures almost all reduce to one meta-problem: tests are coupled to *presentation* (CLI argument grammar, help text formatting, exact error strings) instead of *behavior* (exit codes, file presence, schema validity).** The fixes are:

1. **Helpers** that abstract CLI invocation so argument grammar changes are one-line fixes
2. **Semantic assertions** (`returncode != 0` + key substring) instead of exact string matches
3. **Fixture completeness** (always create entrypoint files alongside manifest YAML)
4. **Kill meta-gate tests** — use pytest markers instead
5. **Enforce deprecation-on-removal** as a workflow rule for PR reviews
6. **Layer tests** by abstraction level so each layer only breaks when its specific contract changes

## Prompt 2 (Human)
> For Recommendation F. Separate schema/unit tests from integration/CLI tests - can you give me a few examples from the existing tests - which tests are schema unit tests and which tests should be integration tests.
>
> For B. Decouple test fixtures from production validation - explain how Option 3: Use validate_manifest_data(data) (which already exists) for schema-only tests, and reserve validate(path) for integration tests that test the full on-disk validation - will look in each case - i.e., a schema-only test that uses validate_manifest_data(data) and an integration test that uses validate(path)
>
> And if fixing F and B, walk me through what the actual refactoring - what will change in the tests/ codebase.
>
> For C. Stop writing regression gate meta-tests - will running ```python3 -m pytest``` still run these marked regression tests? Or do you need to explicitly call the marker like you show in your example.
>
> For E. Adopt a deprecation-on-removal workflow - in conjunction with C, I might suggest to use Python markers to specifically indicate which command this is testing (e.g., @pytest.mark.kinnoo_init) so that, when a feature updates kinnoo init, for example, the agent knows to check if these marked tests are still valid. If this is the case, perhaps we need to create "regression test set" categories and save this somewhere, maybe in tests/ base folder. Each CLI subcommand would definitely be its own test set. I'd need to think about what the other test sets would be.
>
> Don't refactor any test code yet. Respond to my comments above first, and again copy-paste this prompt and your response and append to notes/phases/phase13-uat-2-regression-test-hardening.md.

## Response 2 (Agent)

Excellent direction. Your instincts are right: this is mostly a test architecture problem, not a product-quality problem.

For Recommendation F, here are concrete examples from current tests.

Schema unit tests (should validate manifest rules in memory, with no filesystem contract):
- [tests/test_validator.py](tests/test_validator.py#L146) test_invalid_field_type
- [tests/test_validator.py](tests/test_validator.py#L177) test_invalid_semver_format
- [tests/test_validator.py](tests/test_validator.py#L213) test_framework_optional
- [tests/test_validator.py](tests/test_validator.py#L260) test_feature23_runtime_type_mcp_server_supported

These are schema rule assertions. They are not trying to verify files exist on disk.

Integration validation tests (should use file-backed validation and real paths):
- [tests/test_validator.py](tests/test_validator.py#L48) test_valid_manifest_passes
- [tests/test_validator.py](tests/test_validator.py#L959) test_task489_entrypoints_union_contract_validation
- [tests/test_validator.py](tests/test_validator.py#L981) test_task489_entrypoint_path_missing_reports_deterministic_error

These are explicitly about path-aware behavior and should keep using validate(path).

CLI integration tests (separate from validator schema tests):
- [tests/test_cli_inspect.py](tests/test_cli_inspect.py#L332) test_feature24_inspect_displays_services
- [tests/test_init.py](tests/test_init.py#L210) test_init_minimal_template

These test subprocess invocation, parser behavior, output wiring, and file generation from commands.

For Recommendation B Option 3, here is what each case looks like.

Schema-only test style (validate_manifest_data):

    def test_invalid_semver_schema_only() -> None:
        data = {
            "name": "my-agent",
            "version": "1.0",
            "entrypoint": "run.py",
            "runtime": {"language": "python", "version": ">=3.10", "type": "one-shot"},
            "dependencies": [],
            "inputs": {"type": "text"},
            "outputs": {"type": "text"},
        }
        is_valid, errors = validate_manifest_data(data)
        assert not is_valid
        assert any("semver" in e.lower() for e in errors)

Integration test style (validate(path)):

    def test_entrypoint_path_must_exist(tmp_path: Path) -> None:
        manifest = {
            "name": "my-agent",
            "version": "0.1.0",
            "entrypoint": "run.py",
            "runtime": {"language": "python", "version": ">=3.10", "type": "one-shot"},
            "dependencies": [],
            "inputs": {"type": "text"},
            "outputs": {"type": "text"},
        }
        p = tmp_path / "kinnoo.yaml"
        p.write_text(yaml.dump(manifest), encoding="utf-8")
        # Note: run.py intentionally not created
        is_valid, errors = validate(str(p))
        assert not is_valid
        assert any("Declared entrypoint path not found" in e for e in errors)

Key distinction:
- validate_manifest_data(data) is for schema semantics
- validate(path) is for on-disk semantics (file existence, relative path resolution)

If we fix F and B, this is what will actually change in tests.

1. Split validator tests into layered files:
- tests/test_validator_schema.py for dict-based schema tests
- tests/test_validator_integration.py for file/path behavior

2. Add helper fixtures for intent clarity:
- build_valid_manifest_dict() for schema unit tests
- write_manifest_and_files(tmp_path, manifest, files={...}) for integration tests

3. Migrate existing tests by intent:
- tests that only assert field type/value rules move to validate_manifest_data(data)
- tests that assert entrypoint or entrypoints path behavior remain on validate(path)

4. Keep CLI tests separate:
- no validator internals in CLI subprocess tests
- CLI tests assert command contract and user-facing behavior

This refactor should reduce ghost-breakage because schema tests stop depending on incidental filesystem conditions.

For C (meta-tests and markers), behavior with python3 -m pytest is:
- Yes, python3 -m pytest runs marked tests by default.
- Marker annotations do nothing unless you filter with -m.

So:
- python3 -m pytest runs everything except skipped/xfail rules
- python3 -m pytest -m regression runs only regression-marked tests
- python3 -m pytest -m "not regression" excludes regression-marked tests

For E, your idea to use command-specific markers is exactly right.

I recommend a marker taxonomy like:
- regression dimension: regression, smoke, contract
- surface dimension: kinnoo_init, kinnoo_run, kinnoo_install, kinnoo_pack, kinnoo_inspect, kinnoo_publish, kinnoo_search, kinnoo_login, kinnoo_logout
- layer dimension: schema_unit, integration, cli, e2e
- component dimension: validator, analyzer, registry_client, server_api, web_ui

Then a changed command can drive targeted regression execution. Example:
- if init changes: python3 -m pytest -m "kinnoo_init and (contract or regression)"

Where to store these test-set categories:
- define and document markers in [pyproject.toml](pyproject.toml)
- add practical usage docs in [tests/README.md](tests/README.md)
- optionally add [tests/conftest.py](tests/conftest.py) with shared marker helpers/fixtures

I agree each CLI subcommand should be a first-class test set. Other good sets:
- manifest schema contracts
- filesystem/archive contracts
- remote registry protocol contracts
- auth/session/tenant contracts
- docs contract checks
- migration/deprecation compatibility checks

No refactor has been done yet in this step. This is design guidance only, as requested.
