# Feature62 SWE Handoff

## Scope
- Feature: feature62
- Tasks: task334, task335
- Tests: test493, test494
- Dependencies: none

## Goal
Extend schema and validation to support `openclaw-skill` package type and a `provenance` object with deterministic compatibility rules while keeping metadata intentionally minimal.

## Task Guidance

### task334
Key outcomes:
- Add `openclaw-skill` type support in schema.
- Add `provenance` object keys.
- Enforce framework/type compatibility and `provenance` requirements: `source_registry`, `source_version`, and at least one of `source_slug` or `source_url`.
- Enforce minimal metadata by rejecting `channels`, `skills`, and `state_dirs` fields with deterministic guidance.
- Update schema reference docs with canonical examples.

### task335
Key outcomes:
- Add positive/negative validator fixtures including canonical `provenance` object shapes.
- Add import-path tests asserting deterministic errors on unsupported `provenance` combinations and disallowed metadata fields.
- Add migration guidance for manifests adopting `provenance` object fields.

## AC to Test Mapping
- AC1 -> test493
- AC2 -> test493
- AC3 -> test494
- AC4 -> test494

## Constraints
- Error messages must be specific and actionable.
- Preserve existing manifest compatibility outside OpenClaw-specific branches.
- Contract wording must stay exact: `source_registry`, `source_version`, and at least one of `source_slug` or `source_url`.
