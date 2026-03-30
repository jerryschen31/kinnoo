# Feature75 SWE Handoff

## Scope
- Feature: feature75
- Tasks: task360, task361
- Tests: test519, test520
- Dependencies: none

## Goal
Implement framework-aware import adapters for LangChain, LangGraph, and OpenAI Agents SDK with graceful fallback to generic analysis.

## Task Guidance

### task360
Key outcomes:
- Add `kinnoo import --from langchain|langgraph|openai` parser support.
- Implement adapter modules and integration with import/analyzer flow.
- Ensure fallback to generic analyzer when adapter confidence is insufficient.

### task361
Key outcomes:
- Tune confidence and unresolved-guidance behavior.
- Add fixture coverage for Python and JS/TS-oriented paths.
- Include Vitest-based JS/TS fixture assertions where behavior is JS/TS-specific.

## AC to Test Mapping
- AC1 -> test519
- AC2 -> test519
- AC3 -> test519
- AC4 -> test520

## Constraints
- Maintain deterministic import UX across adapter and fallback paths.
- Vitest automation path must reference concrete function identifiers in `.ts` test files.
