# Feature73 SWE Handoff

## Scope
- Feature: feature73
- Tasks: task356, task357
- Tests: test515, test516
- Dependencies: none

## Goal
Add `kinnoo diff` for package-to-package change inspection with both human-readable and JSON outputs.

## Task Guidance

### task356
Key outcomes:
- Implement archive extraction and structured diff core.
- Report manifest deltas (deps/env/permissions).
- Report file add/remove/modify with deterministic order.

### task357
Key outcomes:
- Add `--json` output with stable schema.
- Implement deterministic exit semantics for identical/different/error.
- Add docs for CI automation usage.

## AC to Test Mapping
- AC1 -> test515
- AC2 -> test515
- AC3 -> test516
- AC4 -> test516

## Constraints
- Keep output deterministic across platforms for CI parity.
- Avoid excessive noise from irrelevant metadata churn.
