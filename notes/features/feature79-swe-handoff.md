# Feature79 SWE Handoff

## Scope
- Feature: feature79
- Tasks: task368, task369
- Tests: test527, test528
- Dependencies: none

## Goal
Ensure OpenClaw workspace packaging includes required identity/memory/skills artifacts and excludes runtime artifacts while preserving installable archive contracts.

## Ordered Implementation Plan
1. Complete task368 first to lock in include rules and fixture coverage for identity/workspace contents.
2. Complete task369 second to enforce excludes, preserve size reporting, and validate JS/TS workspace contract behavior.

## AC to Test Mapping
- AC1 -> test527
- AC2 -> test527
- AC3 -> test528
- AC4 -> test528
- AC5 -> test528

## Design Constraints
- Include identity files deterministically when present.
- Exclude `.git/`, `.openclaw/`, and `node_modules/` reliably.
- Keep the Vitest automation path function-scoped in a `.ts` test file for JS/TS fixture contract validation.