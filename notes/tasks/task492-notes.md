# Task492 Post-Implementation Notes

- Hardened LangChain adapter with sub-package detection, dependency/env-var inference, and viability signals.
- Hardened LangGraph adapter with compile-signal awareness while preserving backward compatibility.
- Hardened OpenAI adapter to distinguish base SDK vs agents SDK behavior and dependency outputs.
- Added regression tests for `test699`, `test700`, and `test701`.

## Teaching Notes

- Adapter hardening works best when detection uses both **import signals** and **behavioral viability signals**.
- Backward compatibility often requires graded confidence instead of strict pass/fail gating.
- When adding framework heuristics, pair them with misclassification guards to prevent regressions.
