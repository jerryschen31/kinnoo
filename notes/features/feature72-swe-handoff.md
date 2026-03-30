# Feature72 SWE Handoff

## Scope
- Feature: feature72
- Tasks: task354, task355
- Tests: test513, test514
- Dependencies: none

## Goal
Provide deterministic lockfile support for reproducible installs and CI-safe frozen resolution.

## Task Guidance

### task354
Key outcomes:
- Implement lockfile schema and write/update behavior.
- Include source/version/checksum/platform metadata.
- Keep output deterministic for repeat runs.

### task355
Key outcomes:
- Implement `kinnoo install --frozen` lockfile-only resolution.
- Fail clearly on drift/missing entries.
- Document regeneration and team workflow guidance.

## AC to Test Mapping
- AC1 -> test513
- AC2 -> test514
- AC3 -> test513
- AC4 -> test514

## Constraints
- Lockfile ordering/schema must remain stable for diff-friendly reviews.
- Frozen mode must never auto-resolve around lockfile drift.
