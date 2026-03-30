# Feature64 SWE Handoff

## Scope
- Feature: feature64
- Tasks: task338, task339
- Tests: test497, test498
- Dependencies: feature62, feature63

## Goal
Enable direct import from ClawHub metadata into local kinnoo projects with canonical manifest scaffolding using the same `provenance` object contract as feature62.

## Task Guidance

### task338
Key outcomes:
- Add `kinnoo import --source clawhub <slug>` command path.
- Resolve mirror metadata with deterministic failure behavior.
- Scaffold `openclaw-skill` manifest with `provenance` object containing `source_registry`, `source_version`, and `source_slug` and/or `source_url` values.
- Save local import report artifact.

### task339
Key outcomes:
- Parse and display requirement hints (env/config/bin).
- Emit unresolved guidance in stable, actionable format.
- Ensure inspect surfaces imported `provenance` object metadata clearly.

## AC to Test Mapping
- AC1 -> test497
- AC2 -> test497
- AC3 -> test498
- AC4 -> test498

## Constraints
- Keep import deterministic for both found and missing slug paths.
- Do not silently drop `provenance` object fields.
- Contract wording must stay exact: `source_registry`, `source_version`, and at least one of `source_slug` or `source_url`.
