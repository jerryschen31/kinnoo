# Feature83 SWE Handoff

> **⚠️ DEPRECATED (2026-04-18):** Feature83 (`kinnoo install --openclaw-skill`) reflects an earlier paradigm where kinnoo treated individual OpenClaw skills from ClawHub as the fundamental unit. **kinnoo now supports OpenClaw workspace-based agents, NOT individual skills.** The `--from openclaw` import flow targets agent workspaces. This handoff document is retained for historical context only.

## Scope
- Feature: feature83
- Tasks: task376, task377
- Tests: test535, test536
- Dependencies: feature76

## Goal
Implement `kinnoo install --openclaw-skill <skill-slug-or-url> <agent-name>` for existing OpenClaw agents with deterministic agent checks, preflight gating, and outcome diagnostics.

## Ordered Implementation Plan
1. Implement task376 first for CLI parsing, target agent resolution, and delegated skill install path.
2. Implement task377 second for slug/URL normalization, gateway-aware preflight, and deterministic outcome reporting.

## AC to Test Mapping
- AC1 -> test535
- AC2 -> test536
- AC3 -> test536
- AC4 -> test535
- AC5 -> test536

## Design Constraints
- If agent is missing, do not attempt install; provide install-agent-first guidance.
- Support slug and URL identifiers in this phase.
- Keep outcome classes explicit: success, already-installed, not-found.