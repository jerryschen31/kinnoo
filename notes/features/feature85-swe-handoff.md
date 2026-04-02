# Feature85 SWE Handoff

## Scope
- Feature: feature85
- Tasks: task380, task381
- Tests: test539, test540
- Dependencies: feature76, feature77, feature78, feature80, feature81

## Goal
Deprecate bridge-era OpenClaw features 62-67 in favor of the CLI-wrapper model while preserving non-breaking compatibility and adding migration warnings/guidance.

## Ordered Implementation Plan
1. Implement task380 first to apply deprecation metadata, update help text, and add migration pointers.
2. Implement task381 second to add runtime deprecation warnings, preserve behavior compatibility, and annotate legacy-path coverage.

## AC to Test Mapping
- AC1 -> test539
- AC2 -> test540
- AC3 -> test539
- AC4 -> test540
- AC5 -> test540
- AC6 -> test539

## Design Constraints
- Keep deprecated flows functional during transition; warnings must be explicit.
- Remove stale help text that implies bridge-first behavior.
- Ensure migration guidance consistently points to feature76-feature84 replacements.