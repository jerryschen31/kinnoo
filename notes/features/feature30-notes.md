# Feature30 Notes

## Intent
Feature30 adds an authenticated web UI for browsing and downloading registry content, aligned with V1 authenticated-only read policy.

## Scope Implemented in Planning
- Updated feature definition and ACs in `FEATURES.txt`
- Added tasks `task245`-`task248`
- Added tests `test343`-`test346`

## UX and Security Model
- Session-authenticated pages only (no anonymous browsing)
- Secure cookies: HttpOnly, Secure, SameSite=Lax
- CSRF tokens required on all POST forms
- Routes:
  - `/login`
  - `/agents`
  - `/agents/{tenant}/{agent}`
  - `/search`

## Task-by-Task Implementation Guidance

### task245
- Configure Jinja2 and static assets.
- Build shared base template and style primitives.
- Keep design simple and maintainable.

### task246
- Implement login/logout session lifecycle.
- Redirect unauthenticated users to `/login`.
- Validate CSRF on form POSTs.

### task247
- Render paginated listing page using server metadata indexes.
- Implement search page and query filtering.
- Ensure only authorized-visible items are shown.

### task248
- Render per-agent profile/version history.
- Provide per-version download actions that redirect via presigned URL route.
- Show stable metadata fields clearly.

## Test Strategy
- `test343`: template engine and base layout
- `test344`: login/logout/session/CSRF
- `test345`: listing + search + auth guard
- `test346`: profile + download redirect flow

## SWE Risks
- Missing session guard on one or more pages
- CSRF checks not applied uniformly to forms
- Template rendering errors on empty states or unknown tenant/agent

## SWE Done Checklist
- Unauthenticated requests redirect to login for all browsing pages
- CSRF validation present for every POST route
- Web UI tests pass with TestClient
- Session invalidation works on logout/password reset paths

## Tech Lead Review 1

### Review Scope and Evidence
- Verified feature/task/test linkage for `feature30` -> `task245`-`task248` -> `test343`-`test346`.
- Reviewed web UI implementation and routes in server app and template stack.
- Executed required gates:
  - `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
  - `python3 -m pytest --testmon` -> `1 failed, 351 passed, 1 skipped`
  - Sensitive-data scan across `server/` for credential/token patterns
  - Large tracked-file scan (>10 MB) via git index

### Feature30 Review Gate
- [x] Scope sanity: Tasks `task245`-`task248` and tests `test343`-`test346` are present and linked.
- [x] Auth-only browsing: unauthenticated `/agents` and `/search` access redirects to `/login`.
- [x] Session + CSRF: login/logout/session lifecycle and CSRF checks are implemented and covered by integration tests.
- [x] UI correctness: listing/search/profile/download pages render expected content and states.
- [x] Download flow: UI download endpoint redirects browser to presigned URL; server does not proxy archive bytes.
- [ ] Approval decision: `BLOCK`.

### AC Coverage Assessment
- AC1: Covered by `test344` (`GET /login`, `POST /login`, session cookie behavior).
- AC2: Covered by `test345` plus template/table implementation for tenant/name/version/author/size/description.
- AC3: Covered by `test346` (profile page and version history rendering).
- AC4: Covered by `test346` (download redirect to storage URL).
- AC5: Covered by `test344` and `test345` (unauthenticated redirect behavior).
- AC6: Covered by `test343` and `test344` (Jinja2/styling and CSRF in POST forms).
- AC7: Covered by `test344`, `test345`, `test346` (TestClient-based auth/session/render flows).

### Findings
1. Merge-blocking regression outside feature30 scope is present in required full run.
  - `python3 -m pytest --testmon` failed on `tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr`.
  - Failure message indicates expected MCP stdout stream line not observed before assertion timeout.
2. Feature30-specific implementation and mapped tests appear consistent with acceptance criteria.
  - No direct functional blockers found in web route/template/session behavior.

### Security and Repository Hygiene
- Sensitive-data scan surfaced expected auth/session/token identifiers and test fixtures; no hardcoded real secrets, tokens, passwords, or private keys identified.
- No git-tracked files larger than 10 MB were found.

### Recommendation
- `BLOCK` for merge to `phase3/main` until the full regression gate is green.
- After fixing the failing MCP regression test, rerun `python3 -m pytest --testmon` and proceed with approval if clean.

## Patch Notes 2026-03-20 (Targeted Regression Fix)

### Context
- Addressed failing regression test: `tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr`.
- Symptom: expected MCP server stdout stream lines were not observed before timeout.

### Root Cause
- `kinnoo run` always bootstrapped an agent-local `.venv` for Python runtime before launching the MCP server.
- For MCP fixtures with empty `requirements.txt`, this startup cost could delay process output long enough to exceed the streaming assertion window.

### Code Changes
- Updated `src/kinnoo/run_command.py`:
  - Computed `runtime_type` earlier so Python runtime setup can branch on runtime mode.
  - Added a fast path for Python `mcp-server` runtime when no dependencies are declared and no `.venv` exists.
  - In that fast path, skipped `.venv` creation and used host interpreter (`sys.executable`) for process launch.
  - Preserved existing `.venv` behavior for all other Python execution paths, including dependency installation flows.

### Verification
- Ran only the mapped failing test as requested:
  - `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr -q`
  - Result: `1 passed in 0.22s`
