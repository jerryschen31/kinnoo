# Feature82 SWE Handoff

## Scope
- Feature: feature82
- Tasks: task374, task375
- Tests: test533, test534
- Dependencies: feature76

## Goal
Add OpenClaw logs passthrough command mode in kinnoo with deterministic preflight and actionable failure diagnostics.

## Ordered Implementation Plan
1. Implement task374 first for command routing and passthrough flags (`--follow`, `--json`).
2. Implement task375 second for preflight enforcement and stable CLI/Gateway error guidance.

## AC to Test Mapping
- AC1 -> test533
- AC2 -> test533
- AC3 -> test534
- AC4 -> test533

## Design Constraints
- Keep this path a thin wrapper around `openclaw logs`.
- Maintain deterministic messaging for missing CLI and RPC failures.
- Preserve passthrough behavior across human and JSON modes.