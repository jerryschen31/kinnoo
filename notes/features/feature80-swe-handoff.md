# Feature80 SWE Handoff

## Scope
- Feature: feature80
- Tasks: task370, task371
- Tests: test529, test530
- Dependencies: feature76, feature79

## Goal
Rework OpenClaw install to extract archives into `~/.openclaw/workspace-<name>/` and register agents through OpenClaw CLI with full kinnoo validation/diagnostics retained.

## Ordered Implementation Plan
1. Implement task370 first for extract target selection, preflight ordering, and `agents add` delegation.
2. Implement task371 second for conflict diagnostics, validation-before-delegation guarantees, and trace output completeness.

## AC to Test Mapping
- AC1 -> test529
- AC2 -> test530
- AC3 -> test529
- AC4 -> test530
- AC5 -> test530

## Design Constraints
- Existing target workspaces must fail safely with remediation guidance.
- Do not bypass kinnoo trust/security checks before delegation.
- Record delegated command outcomes in install diagnostics/traces.