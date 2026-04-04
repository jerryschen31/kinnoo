# Feature66 SWE Handoff

## Scope
- Feature: feature66
- Tasks: task342, task343
- Tests: test501, test502
- Dependencies: feature65

## Goal
Add OpenClaw run adapter v1 so `kinnoo run` can execute OpenClaw skills through version-aware delegation with explicit diagnostics.

## Task Guidance

### task342
Key outcomes:
- Route `openclaw-skill` packages through adapter execution path.
- Detect backend mode by OpenClaw version/capabilities.
- Gate behavior behind explicit experimental compatibility control.
- Emit backend-selection diagnostic logs.

### task343
Key outcomes:
- Add deterministic handling for unsupported versions and missing backends.
- Add tests for success and categorized failure branches.
- Document known adapter limitations and fallback behavior.

## AC to Test Mapping
- AC1 -> test501
- AC2 -> test502
- AC3 -> test501
- AC4 -> test502

## Constraints
- Adapter errors must remain actionable and deterministic.
- Do not silently switch incompatible execution strategies.
