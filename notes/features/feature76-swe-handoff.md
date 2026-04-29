# Feature76 SWE Handoff

## Scope
- Feature: feature76
- Tasks: task362, task363
- Tests: test521, test522
- Dependencies: none

## Goal
Implement a reusable OpenClaw preflight layer that enforces CLI presence/version gating and optional gateway-health checks based on command type.

## Ordered Implementation Plan
1. Implement task362 first to establish a single authoritative preflight module for CLI/version checks.
2. Implement task363 second to wire command handlers to shared preflight and enforce conditional gateway probing.

## AC to Test Mapping
- AC1 -> test521
- AC2 -> test521
- AC3 -> test522
- AC4 -> test522
- AC5 -> test521

## Design Constraints
- OpenClaw version contract is date-based and must support suffixes.
- Keep one reusable preflight module; no duplicated command-local implementations.
- Gateway probe is required only for runtime commands (run/logs/skill flows).