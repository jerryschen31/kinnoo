# Feature74 SWE Handoff

## Scope
- Feature: feature74
- Tasks: task358, task359
- Tests: test517, test518
- Dependencies: feature72

## Goal
Implement safe single-agent uninstall with mandatory user confirmation and consistent metadata cleanup.

## Task Guidance

### task358
Key outcomes:
- Add `kinnoo uninstall <name>` command.
- Require mandatory interactive confirmation.
- Remove target install/runtime artifacts safely.

### task359
Key outcomes:
- Update lockfile/install-trace after uninstall.
- Add deterministic diagnostics for missing-target and partial cleanup failures.
- Keep command scoped to single-agent uninstall only.

## AC to Test Mapping
- AC1 -> test517
- AC2 -> test517
- AC3 -> test518
- AC4 -> test518

## Constraints
- No bulk uninstall command in this phase.
- Confirmation is mandatory and cannot be bypassed in Phase 6.
