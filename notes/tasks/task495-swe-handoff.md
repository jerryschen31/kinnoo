# Task495 SWE Handoff - Import Regression Matrix and Fixture Expansion

## Objective
Expand import hardening regression coverage to maintain a minimum import-related test floor and framework-detection accuracy against realistic fixtures.

## Contract
- Add realistic framework fixtures for supported import surfaces.
- Add framework-accuracy guards (especially LangGraph vs LangChain).
- Enforce and document at least 30 passing import-related tests.

## Primary Files
- `tests/client_cli_import/test_cli_import.py`
- `tests/validator_integration/test_analyzer.py`
- `tests/fixtures/`

## Required Tests
- `test705`

## Execution Guidance
1. Prefer fixtures representing real-world project layouts.
2. Keep tests deterministic and CI-friendly.
3. Capture pass-count evidence in task notes.
