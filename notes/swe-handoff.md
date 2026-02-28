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

