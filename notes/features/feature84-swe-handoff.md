# Feature84 SWE Handoff

> **⚠️ DEPRECATED (2026-04-18):** Feature84 (`kinnoo search --openclaw-skill`) reflects an earlier paradigm where kinnoo treated individual OpenClaw skills from ClawHub as the fundamental unit. **kinnoo now supports OpenClaw workspace-based agents, NOT individual skills.** The `--openclaw-skill` search flag has been removed (see task477). This handoff document is retained for historical context only.

## Scope
- Feature: feature84
- Tasks: task378, task379
- Tests: test537, test538
- Dependencies: feature76

## Goal
Add `kinnoo search --openclaw-skill <query>` as a wrapper over `openclaw skills search` with preflight checks and deterministic empty/error guidance.

## Ordered Implementation Plan
1. Implement task378 first for parser support and search/json delegation behavior.
2. Implement task379 second for preflight failure handling and no-result/upstream-error guidance.

## AC to Test Mapping
- AC1 -> test537
- AC2 -> test538
- AC3 -> test538
- AC4 -> test537

## Design Constraints
- Keep the command a thin wrapper with stable output contracts.
- Preserve JSON passthrough for machine-readable workflows.
- Guidance for empty or failed searches must be deterministic and actionable.