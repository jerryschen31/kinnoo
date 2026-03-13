# SWE Handoff Addendum — Feature10 Secret Non-Disclosure Test Strategy

## Scope
This addendum covers only feature10 security testing for tasks `task53`–`task58` and tests `test78`–`test85`, with emphasis on preventing secret-value disclosure.

## Security invariant (must hold in all paths)
- Secret/env var **values** must never appear in:
	- stdout
	- stderr
	- logs
	- exception traces
	- temp/debug files
- Only env var **names** may be displayed for diagnostics.

## Sentinel-value leak-check pattern (required)
- Use unique sentinel values that are easy to detect, e.g.:
	- `SENTINEL_SECRET_ALPHA_9f3b`
	- `SENTINEL_SECRET_BRAVO_7c21`
- Inject sentinels via all resolution paths:
	1. process environment
	2. `.env` fallback
	3. masked prompt input
- After each run, assert sentinels are absent from:
	- captured stdout/stderr
	- any runtime logs/files touched by the run

## Test implementation notes
- For `test80` / `test82`, simulate prompt input/cancel deterministically; never print entered value.
- For `test84`, add a reusable helper like `assert_no_secret_leak(outputs: list[str], sentinels: list[str])`.
- Use negative assertions (`not in`) for every sentinel across all captured artifacts.
- Verify failure messages reference missing variable names only.

## Task-to-test security focus
- `task53`/`task54`: verify resolution order correctness without value exposure.
- `task55`: verify masked prompt + cancel path with no value echo.
- `task56`: verify subprocess injection works while logs remain value-safe.
- `task57`: enforce and test non-disclosure guardrails (`test84` is mandatory gate).
- `task58`: docs must explicitly state non-disclosure invariant and safe troubleshooting guidance.

## Minimum SWE validation commands
- `python3 -m pytest tests/test_cli_env_vars.py -k "feature10 or env_vars or secret"`
- `python3 -m pytest tests/test_docs.py -k "feature10"`
- `python3 src/validate_project_manifests.py`

## Feature10 docs contract checklist (task58)
- README and schema docs must state resolution order: environment -> .env -> masked prompt.
- Docs must explicitly state secret values are never printed, logged, or persisted.
- Examples and troubleshooting guidance must reference variable names only.

## Follow-up SWE pointers (test86-test88)
- Placeholder pytest functions are already added in `tests/test_cli_env_vars.py` with `[agent]` implementation notes:
	- `test_env_precedence_prefers_process_env_over_dotenv` (implements `test86`)
	- `test_mixed_source_env_var_resolution_and_injection` (implements `test87`)
	- `test_secret_sentinels_absent_from_runtime_artifacts` (implements `test88`)
- Keep these placeholders until full implementations are completed, then remove `@pytest.mark.skip` from each.
- Preserve the non-disclosure invariant in all assertions: secret values must not appear in stdout, stderr, or inspected artifacts.

# TechLead Review — Feature10 (Environment Variable / Secret Management)

Date: 2026-02-28
Reviewer: techlead-agent
Scope: Pre-merge implementation and coverage review for `feature10` before merge back to `phase2/main`

## Executive Summary
- Implementation for `task53`–`task58` is present and behaviorally aligned with feature scope.
- Feature10 runtime and documentation tests pass in focused validation.
- Acceptance criteria coverage is complete for AC1–AC7 via `test78`–`test85`.
- Merge readiness: **Approved with non-blocking improvements**.

## Evidence Reviewed
- Manifest linkage:
	- `FEATURES.txt`: `feature10` links `task53`–`task58`.
	- `TASKS.txt`: task/test mappings for feature10 are present; `task57` and `task58` are `needs-review`.
	- `TESTS.txt`: `test78`–`test85` entries are present with AC mapping.
- Runtime implementation:
	- `src/kinnoo/run_command.py` (env resolution, `.env` fallback, masked prompt, subprocess env injection, safe error path)
	- `src/kinnoo/schema.py` (`normalize_env_vars` runtime normalization)
	- `src/kinnoo/cli.py` (run-command delegation)
- Tests/docs:
	- `tests/test_cli_env_vars.py`
	- `tests/test_docs.py`
	- `README.md`
	- `docs/manifest-schema-reference.md`

## Validation Results
- `python3 -m pytest tests/test_cli_env_vars.py`
	- Result: `7 passed`
- `python3 -m pytest tests/test_cli_env_vars.py tests/test_docs.py -k "feature10 or env_vars or secret"`
	- Result: `8 passed, 1 deselected`
- `python3 src/validate_project_manifests.py`
	- Result: `Validation passed: manifests are consistent`

## AC Coverage Check
- **AC1** env-first resolution path works when declared vars are present in process env → `test78`
- **AC2** `.env` fallback for missing vars works from agent-local file → `test79`
- **AC3** masked interactive prompt path used for unresolved vars → `test80`
- **AC4** resolved vars are injected into subprocess environment → `test81`
- **AC5** cancel/decline aborts with clear missing-variable message → `test82`
- **AC6** agents without `env_vars` remain unaffected (V1 behavior) → `test83`
- **AC7** secret values are not exposed in outputs/docs; names-only guidance maintained → `test84`, `test85`

Coverage verdict: **All feature10 acceptance criteria are covered by automated tests.**

## Gaps / Inconsistencies
1. **Runtime log/file leak assertion is not explicitly implemented in `test84` (non-blocking now)**
	 - `test84` validates captured stdout/stderr with sentinel checks.
	 - Its test description/pass criteria also mention runtime logs/files, but current test does not inspect filesystem artifacts.

2. **Prompt masking behavior is indirectly tested (non-blocking)**
	 - `test80` monkeypatches `getpass.getpass`, which verifies prompt path execution and no value echo in captured output.
	 - It does not directly assert terminal-level character masking behavior (which is delegated to `getpass`).

3. **Task/file scope wording drift for `task57` (process-level inconsistency)**
	 - `task57` lists `install_command.py` and `pack_command.py` in scope, but implemented/tested behavior is concentrated in run-path env handling (`run_command.py`).
	 - This is acceptable for feature10 ACs, but task wording can be tightened for traceability.

## Suggested Improvements
- Add one negative test that verifies no sentinel secret appears in any created temp/log artifacts (if/when logging files are introduced).
- Add a precedence test where the same variable exists in both process env and `.env`, asserting process env wins.
- Add a multi-variable mixed-source test (some env, some `.env`, some prompt) to strengthen regression confidence for ordered resolution.

## Final TechLead Recommendation
- **Approved for merge to `phase2/main`** from a feature10 implementation and AC-coverage standpoint.
- Keep the improvement items as follow-up hardening tasks; none are merge blockers for current feature10 acceptance criteria.

