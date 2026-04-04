# Feature78 SWE Handoff

## Scope
- Feature: feature78
- Tasks: task366, task367
- Tests: test525, test526
- Dependencies: feature76

## Goal
Implement OpenClaw workspace import that infers kinnoo.yaml, supports copy/register workflow for external directories, and reconciles registration for in-place workspaces.

## Ordered Implementation Plan
1. Deliver task366 first to complete detection, inference, and deterministic invalid-source diagnostics.
2. Deliver task367 second to add copy/register prompts, in-place registration reconciliation, and destination conflict handling.

## AC to Test Mapping
- AC1 -> test525
- AC2 -> test526
- AC3 -> test526
- AC4 -> test525
- AC5 -> test525

## Design Constraints
- Preserve analyzer-based weighted detection signals.
- Avoid destructive copy semantics; require explicit operator confirmation.
- Keep registration checks deterministic via `openclaw agents list`/`add` flows.