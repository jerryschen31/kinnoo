# Feature68 SWE Handoff

## Scope
- Feature: feature68
- Tasks: task346, task347
- Tests: test505, test506
- Dependencies: feature61

## Goal
Provide a reliable GitHub Actions reference workflow and docs for CI preflight/pack/publish with strict trust controls.

## Task Guidance

### task346
Key outcomes:
- Add canonical workflow file for install -> preflight -> pack -> publish.
- Document secrets/env contract (registry token, strict-mode controls).
- Ensure failure behavior is deterministic and non-zero in CI.

### task347
Key outcomes:
- Add docs/integrity tests for workflow snippet correctness.
- Keep workflow and README/docs examples in sync.
- Add troubleshooting guidance for common CI failures.

## AC to Test Mapping
- AC1 -> test505
- AC2 -> test506
- AC3 -> test505
- AC4 -> test506

## Constraints
- Never suggest storing credentials in repository files.
- Keep CI guidance compatible with strict mode introduced in feature71.
