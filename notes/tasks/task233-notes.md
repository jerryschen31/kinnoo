# Task233 - feature28 remote client error handling

## Summary
- Added structured, actionable remote error handling in src/kinnoo/remote_client.py.
- Introduced `RemoteRegistryClientError` for expected remote/network failure scenarios so callers receive stable user-facing messages.
- Implemented explicit HTTP status mapping:
  - 401 -> unauthorized guidance (check token / sign in)
  - 403 -> permission guidance
  - 404 -> agent/version/tenant not found guidance
  - 409 -> duplicate/conflict guidance
  - 429 -> retry-after style guidance
  - 5xx -> transient server error guidance
- Implemented connection error handling for connection refused with a clear “server not reachable” message.
- Added fallback network error messaging for other URLError cases.
- Added invalid JSON response guard with clear remediation-oriented message.
- Added mapped test331 in tests/test_remote_client.py as `test_error_handling`.

## Tests and results
- `python3 -m pytest tests/test_remote_client.py::test_error_handling` -> `1 passed`

## Bug/error notes
- Bug class: missing `pytest` import in the newly added unit test.
- Attempts for this bug class: `1` (cap: `5`).
- Resolution: added `import pytest` to tests/test_remote_client.py.

## Teaching notes
- A dedicated typed exception (`RemoteRegistryClientError`) is a good boundary contract: transport/HTTP specifics stay in the client while higher layers can present consistent UX.
- Error mapping should prioritize operator actionability over raw protocol detail. Include both what happened and what to try next.
- Keep expected remote failures out of traceback-heavy paths by raising controlled exceptions for known categories (auth, permission, not found, conflicts, rate limit, transient server errors).
- For resilient CLI UX, separate deterministic status-based mappings (HTTP) from best-effort transport mappings (connection refused and generic network errors).
