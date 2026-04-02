# Feature81 SWE Handoff

## Scope
- Feature: feature81
- Tasks: task372, task373
- Tests: test531, test532
- Dependencies: feature76

## Goal
Implement OpenClaw run wrapper that delegates to `openclaw agent`, enforces gateway-aware preflight, supports thinking passthrough, and maintains deterministic output/error behavior.

## Ordered Implementation Plan
1. Complete task372 first to implement command mapping, thinking passthrough, and exit propagation.
2. Complete task373 second to enforce gateway health gating and support `--json` output passthrough while keeping text input default.

## AC to Test Mapping
- AC1 -> test531
- AC2 -> test532
- AC3 -> test532
- AC4 -> test531
- AC5 -> test531

## Design Constraints
- Keep `kinnoo run` prompt flow text-first in this phase.
- Require gateway health before runtime delegation.
- Do not add JSON input support yet; defer to future feature.