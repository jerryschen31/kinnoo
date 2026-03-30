# Feature67 SWE Handoff

## Scope
- Feature: feature67
- Tasks: task344, task345
- Tests: test503, test504
- Dependencies: feature63

## Goal
Implement `kinnoo sync clawhub` command with incremental/full modes, clawhub-tenant upserts, and resilient diagnostics.

## Task Guidance

### task344
Key outcomes:
- Add command surface for `sync clawhub` with `--full` and incremental options.
- Implement deterministic upsert behavior into clawhub tenant mirror records.
- Emit created/updated/skipped/failure counters.

### task345
Key outcomes:
- Add polite fetch/retry behavior for upstream instability.
- Preserve existing mirror consistency under partial failures.
- Add categorized sync diagnostics and tests.

## AC to Test Mapping
- AC1 -> test503
- AC2 -> test503
- AC3 -> test504
- AC4 -> test504

## Constraints
- Never corrupt existing mirror state on failed sync batches.
- Keep source attribution fields stable on updates.
