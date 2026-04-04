# Feature65 SWE Handoff

## Scope
- Feature: feature65
- Tasks: task340, task341
- Tests: test499, test500
- Dependencies: feature62

## Goal
Support install for OpenClaw skill packages by delegating install execution to OpenClaw CLI while preserving kinnoo trust/validation controls.

## Task Guidance

### task340
Key outcomes:
- Detect `openclaw-skill` package type in install flow.
- Add OpenClaw CLI presence/version checks.
- Delegate install command with explicit diagnostics and traces.
- Preserve kinnoo-side validation around delegation.

### task341
Key outcomes:
- Implement deterministic failure categories for missing runtime/version/CLI errors.
- Add coverage for delegated success and each failure path.
- Update docs with prerequisites and delegated behavior.

## AC to Test Mapping
- AC1 -> test499
- AC2 -> test499
- AC3 -> test500
- AC4 -> test500

## Constraints
- Delegation must not bypass trust and validation guardrails.
- Error output should include concrete remediation steps.
