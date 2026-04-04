# task361 notes

## Summary
- Added adapter confidence tuning utilities in src/kinnoo/analyzer.py for minimum coverage thresholds and default unresolved guidance.
- Updated import adapter application flow in src/kinnoo/import_command.py to use tuned thresholds and emit deterministic fallback diagnostics including score and required threshold.
- Extended unresolved TODO guidance to include adapter-provided unresolved guidance entries.
- Added Python fixture regression coverage in tests/test_cli_import.py for confidence tuning and fallback messaging.
- Added JS/TS Vitest fixture contract suite in web/__tests__/framework-adapter-fixtures.test.ts with stable function identifier `it_langgraph_ts_fixture_maps_adapter_contract`.
- Documented framework adapter best practices and limitations in docs/manifest-schema-reference.md.

## Teaching Notes
- Confidence tuning should be explicit and centralized; exposing threshold helpers in analyzer keeps adapter behavior predictable across future framework additions.
- Adapter fallback messages are most useful when they include both observed score and required threshold.
- Cross-runtime validation should separate concerns: Python integration tests for CLI/import behavior and Vitest fixture contracts for JS/TS mapping expectations.

## Validation
- python3 -m pytest tests --testmon -k test_feature75_adapter_confidence_tuning_and_guidance
- cd web && npm run test -- __tests__/framework-adapter-fixtures.test.ts
