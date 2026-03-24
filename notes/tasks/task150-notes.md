# Task150 - feature25 health-check module and checker primitives

## Summary
- Added new module `src/kinnoo/health_check.py` with a normalized `HealthCheckResult` dataclass and a dispatcher `run_service_health_check(service)`.
- Implemented HTTP health checks with `urllib.request` using default 5s timeout and per-service `timeout_seconds` override.
- Implemented TCP localhost checks with `socket.create_connection` using default 3s timeout and per-service override.
- Implemented process checks using `pgrep -f <pattern>` and actionable failure guidance.
- Added feature25 timeout constants to schema for shared defaults:
  - `DEFAULT_HTTP_HEALTH_CHECK_TIMEOUT_SECONDS = 5.0`
  - `DEFAULT_TCP_HEALTH_CHECK_TIMEOUT_SECONDS = 3.0`
- Added task150 test coverage in `tests/test_health_check.py` for test228/test229/test230.
- Updated `task150` status to `needs-review` in `TASKS.txt`.

## Tests and results
- `python3 -m pytest tests/test_health_check.py` -> `3 passed`

## Bug/error notes
- No repeated bug/error class encountered during task150 implementation.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- A small normalized result model is useful because later orchestration (`run` and `--preflight`) can render and enforce policy without knowing checker internals.
- Timeout defaults belong in shared schema/constants so behavior is consistent and easy to tune across modules and tests.
- For runtime checks, actionable guidance should be part of the result contract, not added ad hoc in the caller. This keeps operator UX predictable.
- In AI-agent systems, this pattern is similar to tool abstraction: each checker is a bounded tool, while orchestration decides policy (continue/abort/prompt). Keeping those concerns separate improves reliability and testability.
