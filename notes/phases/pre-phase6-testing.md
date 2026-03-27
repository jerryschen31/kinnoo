# Pre-Phase 6 Testing: CI and Pytest Failure Diagnosis

_Date: March 27, 2026_

## Scope

Before starting Phase 6 implementation, we investigated failures reported in GitHub Actions run `23632840174` and compared them with local `python3 -m pytest tests` behavior.

## What Was Failing

### GitHub Actions (`gh run view 23632840174 --log-failed`)

Failing tests observed:
1. `tests/test_pack.py::test_feature26_filesystem_mcp_fixture_valid_and_packable`
2. `tests/test_pack.py::test_feature26_github_mcp_fixture_valid_and_packable`
3. `tests/test_registry.py::test_feature26_filesystem_permissions_runtime_enforcement`
4. `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7` (failed because it includes `tests/test_pack.py`)
5. `tests/test_web_frontend_setup.py::test_feature49_task284_placeholder_routes_are_navigable`
6. `tests/test_web_frontend_setup.py::test_feature49_task282_build_and_dev_start`

### Local (`python3 -m pytest tests`) prior to fixes

Local failures were different in details but related in nature:
1. `tests/test_cli.py::test_backend_selection`
2. `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`
3. `tests/test_web_frontend_setup.py::test_feature49_task284_placeholder_routes_are_navigable`

## Root Causes

### Root cause A: Feature26 tests depended on untracked `scratch/` fixtures

`tests/test_pack.py` and `tests/test_registry.py` loaded fixture assets from:
- `scratch/feature26-filesystem-mcp-server`
- `scratch/feature26-github-mcp-server`

Those directories existed locally but were not tracked in git, so CI checkout did not have them, causing `FileNotFoundError`.

### Root cause B: Frontend tests assumed dependencies/backend availability

1. In CI, `next` binary was missing (`sh: 1: next: not found`) because workflow did not install web dependencies.
2. `/registry` route returned HTTP 500 when backend API at `127.0.0.1:8000` was unavailable.
   - `fetchAuthMeServer` threw on connection failure.
   - Auth layout treated this as server error instead of unauthenticated flow.

### Root cause C: `test_backend_selection` was sensitive to project-level publish toggle

`kinnoo-config.txt` has:

```txt
publish_to_authenticated_registry=true
```

So backend selection defaulted to authenticated remote publish behavior unless explicitly isolated, making the unit test brittle.

## Fixes Applied

### 1) Move Feature26 fixtures into tracked test fixtures

Created tracked fixtures under:
- `tests/fixtures/feature26-filesystem-mcp-server/`
- `tests/fixtures/feature26-github-mcp-server/`

Added in both directories:
- `kinnoo.yaml`
- `run.py`
- `requirements.txt`

Updated tests to reference `tests/fixtures/...` instead of `scratch/...`:
- `tests/test_pack.py`
- `tests/test_registry.py`

Also added explicit fixture existence assertions for clearer failure messages.

### 2) Make `test_backend_selection` deterministic

Updated `tests/test_cli.py` to monkeypatch publish behavior config for this test:
- force `publish_to_authenticated_registry=False`

This isolates the test from repository/project-level toggle state.

### 3) Make auth flow resilient when backend is unavailable

Updated:
- `web/lib/auth-client.ts`
- `web/app/(auth)/layout.tsx`

Changes:
1. `fetchAuthMeServer` now catches fetch/network errors and returns `{ ok: false, status: 503 }`.
2. Auth layout redirects to `/login` for non-OK auth states (except 429 rate-limit), avoiding 500 on missing backend.

Result: `/registry` behaves as unauthenticated flow in dev/CI instead of crashing.

### 4) Fix CI workflow setup for frontend integration tests

Updated `.github/workflows/ci.yml`:
1. Added Node setup via `actions/setup-node@v4` using `web/.nvmrc`.
2. Enabled npm cache keyed by `web/package-lock.json`.
3. Added `npm ci` in `web/` before running pytest.

This ensures `npm run build` and `npm run dev` tests have required dependencies.

## Validation Results

### Targeted failing tests (post-fix)

Command:

```bash
python3 -m pytest \
  tests/test_pack.py::test_feature26_filesystem_mcp_fixture_valid_and_packable \
  tests/test_pack.py::test_feature26_github_mcp_fixture_valid_and_packable \
  tests/test_registry.py::test_feature26_filesystem_permissions_runtime_enforcement \
  tests/test_cli.py::test_backend_selection \
  tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 \
  tests/test_web_frontend_setup.py::test_feature49_task284_placeholder_routes_are_navigable \
  tests/test_web_frontend_setup.py::test_feature49_task282_build_and_dev_start
```

Result:
- `7 passed`

### Full suite validation

Command:

```bash
python3 -m pytest tests
```

Result:
- `450 passed, 1 skipped`

## Conclusion

The failures were a mix of:
1. test fixture portability issues,
2. CI environment setup gaps,
3. one frontend runtime resilience gap,
4. one unit test isolation issue.

All identified failures are now mitigated with deterministic fixtures, CI setup hardening, and resilient auth behavior for backend-unavailable scenarios.

This clears the test baseline so we can start Phase 6 with stable CI and reproducible local test runs.
