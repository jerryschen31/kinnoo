# Feature71 SWE Handoff

## Scope
- Feature: feature71
- Tasks: task352, task353
- Tests: test511, test512
- Dependencies: none

## Goal
Enforce signed-package requirements on automation paths via strict mode for install and publish commands.

## Task Guidance

### task352
Key outcomes:
- Implement `kinnoo install --strict` gate.
- Reject unsigned/invalid signatures deterministically.
- Disallow unsafe override paths in strict mode.

### task353
Key outcomes:
- Implement `kinnoo publish --strict` gate.
- Add rollout guidance in CI workflow/docs.
- Add tests for strict pass/fail and remediation messages.

## AC to Test Mapping
- AC1 -> test511
- AC2 -> test512
- AC3 -> test511
- AC4 -> test512

## Constraints
- Strict mode must fail closed with clear remediation text.
- Keep non-strict behavior unchanged for backward compatibility.
