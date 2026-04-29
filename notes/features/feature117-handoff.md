# Feature117 Handoff - Pre-release Feature 6 Import Hardening (Phase14)

## Scope
Feature117 translates PRE-RELEASE feature 6 into executable implementation units for SWE and test agents. It focuses on hardening existing `kinnoo import` behavior rather than rewriting it.

## Task Breakdown
- `task491`: Core import error hardening + manifest validation gate
- `task492`: Framework adapter hardening (LangChain, LangGraph, OpenAI)
- `task493`: OpenClaw workspace import flow (`--from openclaw`)
- `task494`: Poetry + generic LLM dependency/env-var inference improvements
- `task495`: Import regression matrix expansion + coverage floor guard

## Test Coverage
- `test696`-`test705` map directly to `feature117` AC1-AC10.
- Coverage includes edge cases, adapter-specific contracts, OpenClaw copy rules, dependency inference, and coverage-floor enforcement.

## Sequencing Guidance
1. Execute `task491` first to stabilize baseline error/validation behavior.
2. Parallelize `task492` and `task493` after task491 baseline is merged.
3. Execute `task494` after task492 to leverage adapter signal improvements.
4. Execute `task495` last to consolidate fixture and regression matrix validation.

## Release-Risk Notes
- Highest risk: framework misclassification and OpenClaw source/target path handling.
- Mitigation: enforce deterministic error contracts and run import/analyzer subsets at each task boundary.
