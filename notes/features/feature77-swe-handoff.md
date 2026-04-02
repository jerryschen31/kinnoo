# Feature77 SWE Handoff

## Scope
- Feature: feature77
- Tasks: task364, task365
- Tests: test523, test524
- Dependencies: feature76

## Goal
Rework OpenClaw init to delegate agent creation to `openclaw agents add` and generate a valid kinnoo manifest in the resulting workspace.

## Ordered Implementation Plan
1. Complete task364 first to implement delegation, preflight ordering, and existing-workspace safety checks.
2. Complete task365 second to generate kinnoo.yaml and print deterministic operator summary guidance.

## AC to Test Mapping
- AC1 -> test523
- AC2 -> test524
- AC3 -> test523
- AC4 -> test523
- AC5 -> test524

## Design Constraints
- Use workspace convention `~/.openclaw/workspace-<name>`.
- Never overwrite existing workspaces.
- Preflight must execute before any subprocess or file mutation.