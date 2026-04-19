# Feature66 SWE Handoff

> **⚠️ PARTIALLY DEPRECATED (2026-04-18):** The "OpenClaw skill" routing described below reflects an earlier paradigm where `openclaw-skill` was the fundamental unit. kinnoo now supports OpenClaw workspace-based agents. The run adapter may still be relevant for executing openclaw-framework agents, but the skill-specific routing and ClawHub-based concepts are deprecated.

## Scope
- Feature: feature66
- Tasks: task342, task343
- Tests: test501, test502
- Dependencies: feature65

## Goal
Add OpenClaw run adapter v1 so `kinnoo run` can execute OpenClaw skills through version-aware delegation with explicit diagnostics.

## Task Guidance

### task342
Key outcomes:
- Route `openclaw-skill` packages through adapter execution path.
- Detect backend mode by OpenClaw version/capabilities.
- Gate behavior behind explicit experimental compatibility control.
- Emit backend-selection diagnostic logs.

### task343
Key outcomes:
- Add deterministic handling for unsupported versions and missing backends.
- Add tests for success and categorized failure branches.
- Document known adapter limitations and fallback behavior.

## AC to Test Mapping
- AC1 -> test501
- AC2 -> test502
- AC3 -> test501
- AC4 -> test502

## Constraints
- Adapter errors must remain actionable and deterministic.
- Do not silently switch incompatible execution strategies.
