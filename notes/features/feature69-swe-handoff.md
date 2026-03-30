# Feature69 SWE Handoff

## Scope
- Feature: feature69
- Tasks: task348, task349
- Tests: test507, test508
- Dependencies: none

## Goal
Implement `kinnoo test` with a standardized, low-friction test format for AI agents that works consistently for Python and JS/TS runtimes.

## Standard Test Format (Phase 6 decision)
Use `kinnoo.tests.yaml` as the canonical file format:
- `version`
- `tests[]`
: `id`, `name`, `input`, `assertions`, `timeout_seconds`, `expected_exit_code`
- Optional tags/metadata for CI grouping

Design principles:
- Human-readable and short
- Deterministic assertions (contains/regex/equals/exit-code)
- Easy for AI agents to generate and maintain

## Task Guidance

### task348
Key outcomes:
- Define and validate `kinnoo.tests.yaml` schema.
- Add parser with deterministic validation diagnostics.
- Support inline/linked test declarations without ambiguity.

### task349
Key outcomes:
- Implement execution engine and `N/M passed` summary.
- Normalize one-shot vs daemon-compatible execution output.
- Add docs/examples for both Python and JS/TS agent workflows.

## AC to Test Mapping
- AC1 -> test507
- AC2 -> test507
- AC3 -> test508
- AC4 -> test508

## Constraints
- Keep format stable and versioned from day one.
- Prefer deterministic assertions over brittle semantic checks in Phase 6.
