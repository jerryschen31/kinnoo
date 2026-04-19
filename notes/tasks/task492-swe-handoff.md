# Task492 SWE Handoff - Framework Adapter Hardening (LangChain/LangGraph/OpenAI)

## Objective
Harden framework adapters to improve detection fidelity, dependency/env-var inference, and structural viability checks for LangChain, LangGraph, and OpenAI/OpenAI Agents SDK projects.

## Contract
- Detect LangChain sub-packages (`langchain_openai`, `langchain_anthropic`, etc.).
- Detect LangGraph graph-construction/compile signals in Python and Node paths.
- Distinguish OpenAI base SDK from Agents SDK and enforce Agents-sdk viability checks.
- Prevent LangGraph/LangChain misclassification regressions.

## Primary Files
- `src/kinnoo/framework_adapters/langchain_adapter.py`
- `src/kinnoo/framework_adapters/langgraph_adapter.py`
- `src/kinnoo/framework_adapters/openai_adapter.py`
- `src/kinnoo/analyzer.py`
- `tests/client_cli_import/test_cli_import.py`
- `tests/validator_integration/test_analyzer.py`

## Required Tests
- `test699`
- `test700`
- `test701`

## Execution Guidance
1. Keep adapter output deterministic and additive to existing analyzer behavior.
2. Prefer warning-first behavior on partial signals over hard failure where possible.
3. Run analyzer/import-focused subsets and record fixture coverage evidence.
